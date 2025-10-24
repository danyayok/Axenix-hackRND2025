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

router = APIRouter()


@router.websocket("/ws/rooms/{room_slug}")
async def ws_room(
    websocket: WebSocket,
    room_slug: str,
    user_id: int = Query(..., description="ID пользователя"),
    invite_key: Optional[str] = Query(None, description="Для приватных комнат"),
):
    """
    Контракт:
      - JOIN:   сервер шлёт {"type":"joined", "room_slug", "user_id"} и затем {"type":"state.snapshot", ...}
      - SIGNAL: {"type":"offer|answer|ice", "to":<user_id>, ...} → to-one, сервер добавляет {"from": <sender>}
      - CHAT:   {"type":"chat.message", "text": "..."} → сохраняется и рассылается всем
      - STATE:  {"type":"state.set", topic?, is_locked?, mute_all?} → broadcast "state.changed"
                {"type":"hand.raise"} / {"type":"hand.lower"} → broadcast "hand.raised/hand.lowered"
      - LEAVE:  {"type":"leave"} → закрытие; также закрывается по разрыву сокета
    """
    await websocket.accept()

    # отдельная async-сессия на жизнь сокета
    db: AsyncSession = SessionLocal()
    svc_part = ParticipantService(MembershipRepository(db), RoomRepository(db), UserRepository(db))
    svc_chat = ChatService(MessageRepository(db), RoomRepository(db), UserRepository(db))
    svc_state = StateService(RoomRepository(db), MembershipRepository(db))

    try:
        # ---- JOIN ----
        try:
            await svc_part.join(room_slug=room_slug, user_id=user_id, invite_key=invite_key)
        except ValueError as e:
            await _safe_json_send(websocket, {"type": "error", "reason": str(e)})
            await _safe_close(websocket, status.WS_1008_POLICY_VIOLATION)
            return

        await HUB.join(room_slug, user_id, websocket)
        await _safe_json_send(websocket, {"type": "joined", "room_slug": room_slug, "user_id": user_id})
        # снапшот состояния сразу подключившемуся
        snap = await svc_state.snapshot(room_slug)
        await _safe_json_send(websocket, {"type": "state.snapshot", **snap})
        # уведомим остальных о входе
        await HUB.broadcast(room_slug, {"type": "member.joined", "user_id": user_id}, exclude={user_id})

        # ---- LOOP ----
        while True:
            raw = await websocket.receive_text()
            await svc_part.heartbeat(room_slug=room_slug, user_id=user_id)

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

            # --- Chat (broadcast & persist) ---
            if mtype == "chat.message":
                text = msg.get("text", "")
                try:
                    saved = await svc_chat.send(room_slug=room_slug, user_id=user_id, text=text)
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

            # --- Room state (topic / lock / mute_all) ---
            if mtype == "state.set":
                changed = False
                latest = None

                if "topic" in msg:
                    latest = await svc_state.set_topic(room_slug, msg.get("topic"))
                    changed = True
                if "is_locked" in msg:
                    latest = await svc_state.set_locked(room_slug, bool(msg.get("is_locked")))
                    changed = True
                if "mute_all" in msg:
                    latest = await svc_state.set_mute_all(room_slug, bool(msg.get("mute_all")))
                    changed = True

                if changed and latest is not None:
                    await HUB.broadcast(room_slug, {"type": "state.changed", **latest})
                continue

            # --- Raised hands ---
            if mtype == "hand.raise":
                latest = await svc_state.set_hand(room_slug, user_id, True)
                await HUB.broadcast(room_slug, {"type": "hand.raised", "user_id": user_id, **latest})
                continue

            if mtype == "hand.lower":
                latest = await svc_state.set_hand(room_slug, user_id, False)
                await HUB.broadcast(room_slug, {"type": "hand.lowered", "user_id": user_id, **latest})
                continue

            # --- Leave ---
            if mtype == "leave":
                break

            # неизвестные типы молча игнорируем

    except (WebSocketDisconnect, SWebSocketDisconnect):
        pass
    finally:
        try:
            await svc_part.leave(room_slug=room_slug, user_id=user_id)
            await HUB.leave(room_slug, user_id)
            await HUB.broadcast(room_slug, {"type": "member.left", "user_id": user_id})
            await _safe_close(websocket, status.WS_1000_NORMAL_CLOSURE)
        finally:
            await db.close()  # закрываем async session


async def _safe_json_send(ws: WebSocket, data: dict) -> None:
    if ws.client_state == WebSocketState.CONNECTED:
        await ws.send_json(data)


async def _safe_close(ws: WebSocket, code: int) -> None:
    if ws.client_state == WebSocketState.CONNECTED:
        await ws.close(code=code)
