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
from app.services.participants import ParticipantService
from app.services.chat import ChatService
from app.services.state import StateService
from app.core.security import get_user_id_from_token

router = APIRouter()


@router.websocket("/ws/rooms/{room_slug}")
async def ws_room(
    websocket: WebSocket,
    room_slug: str,
    token: str = Query(..., description="JWT access token (guest)"),
    invite_key: Optional[str] = Query(None, description="Для приватных комнат"),
):
    """
    WS контракт (сокр.):
      - Авторизация: ?token=JWT; uid берётся из токена.
      - JOIN → 'joined', затем 'state.snapshot' (и broadcast 'member.joined').
      - WebRTC: 'offer'/'answer'/'ice' с полем 'to' → сервер пересылает адресату, добавляя 'from'.
      - Chat: 'chat.message' → сохраняем и рассылаем.
      - State: 'state.set' (topic/is_locked/mute_all) — только owner/host → broadcast 'state.changed'.
      - Hands: 'hand.raise' / 'hand.lower' → broadcast с актуальным снапшотом.
      - LEAVE: 'leave' или разрыв соединения.
    """
    await websocket.accept()

    # validate token -> uid
    try:
        user_id = get_user_id_from_token(token)
    except Exception:
        await _safe_json_send(websocket, {"type": "error", "reason": "invalid_token"})
        await _safe_close(websocket, status.WS_1008_POLICY_VIOLATION)
        return

    # одна async-сессия на жизнь сокета
    db: AsyncSession = SessionLocal()
    svc_part = ParticipantService(MembershipRepository(db), RoomRepository(db), UserRepository(db))
    svc_chat = ChatService(MessageRepository(db), RoomRepository(db), UserRepository(db))
    svc_state = StateService(RoomRepository(db), MembershipRepository(db))

    try:
        # ---- JOIN (с учётом private/lock) ----
        try:
            await svc_part.join(room_slug=room_slug, user_id=user_id, invite_key=invite_key)
            await db.commit()  # важно зафиксировать join
        except ValueError as e:
            await _safe_json_send(websocket, {"type": "error", "reason": str(e)})
            await _safe_close(websocket, status.WS_1008_POLICY_VIOLATION)
            return

        await HUB.join(room_slug, user_id, websocket)
        await _safe_json_send(websocket, {"type": "joined", "room_slug": room_slug, "user_id": user_id})

        # снапшот состояния подключившемуся
        snap = await svc_state.snapshot(room_slug)
        await _safe_json_send(websocket, {"type": "state.snapshot", **snap})

        # известим остальных
        await HUB.broadcast(room_slug, {"type": "member.joined", "user_id": user_id}, exclude={user_id})

        # ---- MAIN LOOP ----
        while True:
            raw = await websocket.receive_text()

            # heartbeat не меняет данные, но обновляет last_seen
            await svc_part.heartbeat(room_slug=room_slug, user_id=user_id)
            await db.commit()  # фиксируем heartbeat (last_seen)

            # разбор JSON
            try:
                msg = json.loads(raw)
                if not isinstance(msg, dict) or "type" not in msg:
                    raise ValueError("bad_payload")
            except Exception:
                await _safe_json_send(websocket, {"type": "error", "reason": "bad_json"})
                continue

            mtype = msg.get("type")

            # --- WebRTC signaling (to-one) ---
            if mtype in ("offer", "answer", "ice"):
                to_uid = msg.get("to")
                if not isinstance(to_uid, int):
                    await _safe_json_send(websocket, {"type": "error", "reason": "missing_to"})
                    continue
                payload: Dict[str, Any] = {k: v for k, v in msg.items() if k not in ("type", "to")}
                payload.update({"type": mtype, "from": user_id})
                await HUB.send_to(room_slug, to_uid, payload)
                continue

            # --- Chat (persist + broadcast) ---
            if mtype == "chat.message":
                text = msg.get("text", "")
                try:
                    saved = await svc_chat.send(room_slug=room_slug, user_id=user_id, text=text)
                    await db.commit()  # фиксируем сохранённое сообщение
                except ValueError as e:
                    await _safe_json_send(websocket, {"type": "error", "reason": str(e)})
                    continue

                payload = {
                    "type": "chat.message",
                    "id": saved.id,
                    "room_slug": room_slug,
                    "user_id": user_id,
                    "text": saved.text,
                    "created_at": saved.created_at.isoformat() + "Z",
                }
                await HUB.broadcast(room_slug, payload)
                continue

            # --- State.set (topic/lock/mute_all) — только owner/host ---
            if mtype == "state.set":
                # узнаём роль отправителя
                room = await RoomRepository(db).get_by_slug(room_slug)
                membership = await MembershipRepository(db).get_active(room_id=room.id, user_id=user_id) if room else None
                role = membership.role if membership else "guest"
                if role not in ("owner", "host"):
                    await _safe_json_send(websocket, {"type": "error", "reason": "forbidden"})
                    continue

                changed = False
                latest = None
                if "topic" in msg:
                    latest = await svc_state.set_topic(room_slug, msg.get("topic"))
                    await db.commit()
                    changed = True
                if "is_locked" in msg:
                    latest = await svc_state.set_locked(room_slug, bool(msg.get("is_locked")))
                    await db.commit()
                    changed = True
                if "mute_all" in msg:
                    latest = await svc_state.set_mute_all(room_slug, bool(msg.get("mute_all")))
                    await db.commit()
                    changed = True

                if changed and latest is not None:
                    await HUB.broadcast(room_slug, {"type": "state.changed", **latest})
                continue

            # --- Raised hands (любой участник) ---
            if mtype == "hand.raise":
                latest = await svc_state.set_hand(room_slug, user_id, True)
                await db.commit()
                await HUB.broadcast(room_slug, {"type": "hand.raised", "user_id": user_id, **latest})
                continue

            if mtype == "hand.lower":
                latest = await svc_state.set_hand(room_slug, user_id, False)
                await db.commit()
                await HUB.broadcast(room_slug, {"type": "hand.lowered", "user_id": user_id, **latest})
                continue

            # --- Leave ---
            if mtype == "leave":
                break

            # неизвестные типы — игнор

    except (WebSocketDisconnect, SWebSocketDisconnect):
        pass
    finally:
        try:
            # снимем участника с онлайна
            await svc_part.leave(room_slug=room_slug, user_id=user_id)
            await db.commit()
            await HUB.leave(room_slug, user_id)
            await HUB.broadcast(room_slug, {"type": "member.left", "user_id": user_id})
            await _safe_close(websocket, status.WS_1000_NORMAL_CLOSURE)
        finally:
            await db.close()


async def _safe_json_send(ws: WebSocket, data: dict) -> None:
    if ws.client_state == WebSocketState.CONNECTED:
        await ws.send_json(data)


async def _safe_close(ws: WebSocket, code: int) -> None:
    if ws.client_state == WebSocketState.CONNECTED:
        await ws.close(code=code)
