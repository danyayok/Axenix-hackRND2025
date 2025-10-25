from typing import Optional, Any, Dict
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from fastapi.websockets import WebSocketState
from starlette.websockets import WebSocketDisconnect as SWebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ws_hub import HUB
from app.db.session import SessionLocal
from app.repositories.membership_repo import MembershipRepository
from app.repositories.room_repo import RoomRepository
from app.repositories.user_repo import UserRepository
from app.repositories.message_repo import MessageRepository
from app.repositories.event_repo import EventRepository
from app.services.participants import ParticipantService
from app.services.chat import ChatService
from app.services.state import StateService
from app.services.media import MediaService
from app.services.sync import SyncService
from app.core.security import get_user_id_from_token

router = APIRouter()

@router.websocket("/ws/rooms/{room_slug}")
async def ws_room(
    websocket: WebSocket,
    room_slug: str,
    token: str = Query(..., description="JWT access token (guest)"),
    invite_key: Optional[str] = Query(None, description="Для приватных комнат"),
):
    await websocket.accept()

    try:
        user_id = get_user_id_from_token(token)
    except Exception:
        await _safe_json_send(websocket, {"type": "error", "reason": "invalid_token"})
        await _safe_close(websocket, status.WS_1008_POLICY_VIOLATION)
        return

    db: AsyncSession = SessionLocal()
    rrepo = RoomRepository(db)
    mrepo = MembershipRepository(db)
    erepo = EventRepository(db)

    svc_part = ParticipantService(mrepo, rrepo, UserRepository(db))
    svc_chat = ChatService(MessageRepository(db), rrepo, UserRepository(db))
    svc_state = StateService(rrepo, mrepo)
    svc_media = MediaService(rrepo, mrepo)
    svc_sync = SyncService(rrepo, erepo)

    try:
        # JOIN
        try:
            await svc_part.join(room_slug=room_slug, user_id=user_id, invite_key=invite_key)
            await db.commit()
        except ValueError as e:
            await _safe_json_send(websocket, {"type": "error", "reason": str(e)})
            await _safe_close(websocket, status.WS_1008_POLICY_VIOLATION)
            return

        await HUB.join(room_slug, user_id, websocket)
        await _safe_json_send(websocket, {"type": "joined", "room_slug": room_slug, "user_id": user_id})
        snap = await svc_state.snapshot(room_slug)
        await _safe_json_send(websocket, {"type": "state.snapshot", **snap})
        next_seq = await svc_sync.next_seq()
        await _safe_json_send(websocket, {"type": "sync.info", "next_seq": next_seq})

        await HUB.broadcast(room_slug, {"type": "member.joined", "user_id": user_id}, exclude={user_id})
        ev = await svc_sync.append(room_slug=room_slug, type_="member.joined", payload={"user_id": user_id})
        await db.commit()

        while True:
            raw = await websocket.receive_text()

            await svc_part.heartbeat(room_slug=room_slug, user_id=user_id)
            await db.commit()

            try:
                msg = json.loads(raw)
                if not isinstance(msg, dict) or "type" not in msg:
                    raise ValueError("bad_payload")
            except Exception:
                await _safe_json_send(websocket, {"type": "error", "reason": "bad_json"})
                continue

            mtype = msg.get("type")

            room = await rrepo.get_by_slug(room_slug)
            membership = await mrepo.get_active(room_id=room.id, user_id=user_id) if room else None
            role = membership.role if membership else "guest"
            mute_all = bool(room.mute_all) if room else False
            admin_muted = bool(membership.admin_muted) if membership else False
            is_privileged = role in ("owner", "admin")

            if (mute_all and not is_privileged) or admin_muted:
                if mtype in ("offer", "answer", "ice", "chat.message", "chat.message.enc"):
                    await _safe_json_send(websocket, {"type": "error", "reason": "muted_by_admin"})
                    continue

            # SYNC subscribe
            if mtype == "sync.sub":
                after_seq = int(msg.get("after_seq", 0))
                items = await svc_sync.list_after(room_slug=room_slug, after_seq=after_seq, limit=int(msg.get("limit", 200)))
                await _safe_json_send(websocket, {"type": "sync.batch", "items": items})
                continue

            # signaling
            if mtype in ("offer", "answer", "ice"):
                to_uid = msg.get("to")
                if not isinstance(to_uid, int):
                    await _safe_json_send(websocket, {"type": "error", "reason": "missing_to"})
                    continue
                payload: Dict[str, Any] = {k: v for k, v in msg.items() if k not in ("type", "to")}
                payload.update({"type": mtype, "from": user_id})
                await HUB.send_to(room_slug, to_uid, payload)
                continue

            # chat (plaintext)
            if mtype == "chat.message":
                text = msg.get("text", "")
                try:
                    saved = await svc_chat.send(room_slug=room_slug, user_id=user_id, text=text)
                    await db.commit()
                except ValueError as e:
                    await _safe_json_send(websocket, {"type": "error", "reason": str(e)})
                    continue

                ev = await svc_sync.append(
                    room_slug=room_slug, type_="chat.message",
                    payload={
                        "id": saved.id,
                        "room_slug": room_slug,
                        "user_id": user_id,
                        "text": saved.text,
                        "created_at": saved.created_at.isoformat() + "Z",
                    }
                )
                await db.commit()
                await HUB.broadcast(room_slug, {"type": "chat.message", "seq": ev.id, "id": saved.id,
                                                "room_slug": room_slug, "user_id": user_id,
                                                "text": saved.text, "created_at": saved.created_at.isoformat() + "Z"})
                continue

            # chat (encrypted)
            if mtype == "chat.message.enc":
                b64 = msg.get("ciphertext_b64", "")
                algo = msg.get("algo", "AES-256-GCM")
                try:
                    saved = await svc_chat.send_encrypted(room_slug=room_slug, user_id=user_id, b64_cipher=b64, algo=algo)
                    await db.commit()
                except ValueError as e:
                    await _safe_json_send(websocket, {"type": "error", "reason": str(e)})
                    continue

                ev = await svc_sync.append(
                    room_slug=room_slug, type_="chat.message.enc",
                    payload={
                        "id": saved.id,
                        "room_slug": room_slug,
                        "user_id": user_id,
                        "algo": saved.enc_algo,
                        "ciphertext_b64": saved.text,
                        "created_at": saved.created_at.isoformat() + "Z",
                    }
                )
                await db.commit()
                await HUB.broadcast(room_slug, {"type": "chat.message.enc", "seq": ev.id,
                                                "id": saved.id, "room_slug": room_slug, "user_id": user_id,
                                                "algo": saved.enc_algo, "ciphertext_b64": saved.text,
                                                "created_at": saved.created_at.isoformat() + "Z"})
                continue

            # typing
            if mtype == "chat.typing":
                is_typing = bool(msg.get("is_typing", True))
                await HUB.broadcast(room_slug, {"type": "chat.typing", "user_id": user_id, "is_typing": is_typing}, exclude={user_id})
                continue

            # state.set (owner/admin)
            if mtype == "state.set":
                if not is_privileged:
                    await _safe_json_send(websocket, {"type": "error", "reason": "forbidden"})
                    continue
                changed = False
                latest = None
                if "topic" in msg:
                    latest = await svc_state.set_topic(room_slug, msg.get("topic")); await db.commit(); changed = True
                if "is_locked" in msg:
                    latest = await svc_state.set_locked(room_slug, bool(msg.get("is_locked"))); await db.commit(); changed = True
                if "mute_all" in msg:
                    latest = await svc_state.set_mute_all(room_slug, bool(msg.get("mute_all"))); await db.commit(); changed = True
                if changed and latest is not None:
                    ev = await svc_sync.append(room_slug=room_slug, type_="state.changed", payload=latest)
                    await db.commit()
                    await HUB.broadcast(room_slug, {"type": "state.changed", "seq": ev.id, **latest})
                continue

            # self media
            if mtype == "media.self":
                mic_muted = msg.get("mic_muted", None)
                cam_off = msg.get("cam_off", None)
                if admin_muted and mic_muted is False:
                    await _safe_json_send(websocket, {"type": "error", "reason": "admin_muted"})
                    continue
                state = await svc_media.update_self(room_slug=room_slug, user_id=user_id, mic_muted=mic_muted, cam_off=cam_off)
                await db.commit()
                ev = await svc_sync.append(room_slug=room_slug, type_="media.updated", payload=state)
                await db.commit()
                await HUB.broadcast(room_slug, {"type": "media.updated", "seq": ev.id, **state})
                continue

            # hands
            if mtype == "hand.raise":
                latest = await svc_state.set_hand(room_slug, user_id, True); await db.commit()
                ev = await svc_sync.append(room_slug=room_slug, type_="hand.raised", payload={"user_id": user_id, **latest})
                await db.commit()
                await HUB.broadcast(room_slug, {"type": "hand.raised", "seq": ev.id, "user_id": user_id, **latest})
                continue

            if mtype == "hand.lower":
                latest = await svc_state.set_hand(room_slug, user_id, False); await db.commit()
                ev = await svc_sync.append(room_slug=room_slug, type_="hand.lowered", payload={"user_id": user_id, **latest})
                await db.commit()
                await HUB.broadcast(room_slug, {"type": "hand.lowered", "seq": ev.id, "user_id": user_id, **latest})
                continue

            if mtype == "leave":
                break

    except (WebSocketDisconnect, SWebSocketDisconnect):
        pass
    finally:
        try:
            await svc_part.leave(room_slug=room_slug, user_id=user_id)
            await db.commit()
            await HUB.leave(room_slug, user_id)
            ev = await svc_sync.append(room_slug=room_slug, type_="member.left", payload={"user_id": user_id})
            await db.commit()
            await HUB.broadcast(room_slug, {"type": "member.left", "seq": ev.id, "user_id": user_id})
            await _safe_close(websocket, status.WS_1000_NORMAL_CLOSURE)
        finally:
            await db.close()

async def _safe_json_send(ws: WebSocket, data: dict) -> None:
    if ws.client_state == WebSocketState.CONNECTED:
        await ws.send_json(data)

async def _safe_close(ws: WebSocket, code: int) -> None:
    if ws.client_state == WebSocketState.CONNECTED:
        await ws.close(code=code)
