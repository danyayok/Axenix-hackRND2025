from typing import Optional, Any, Dict
import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from fastapi.websockets import WebSocketState
from starlette.websockets import WebSocketDisconnect as SWebSocketDisconnect

from app.services.ws_hub import HUB
from app.db.session import SessionLocal
from app.repositories.membership_repo import MembershipRepository
from app.repositories.room_repo import RoomRepository
from app.repositories.user_repo import UserRepository
from app.services.participants import ParticipantService

router = APIRouter()

async def _participant_service() -> ParticipantService:
    # создаём сессию на время коннекта
    session = SessionLocal()
    return ParticipantService(
        MembershipRepository(session),
        RoomRepository(session),
        UserRepository(session),
    )

@router.websocket("/ws/rooms/{room_slug}")
async def ws_room(
    websocket: WebSocket,
    room_slug: str,
    user_id: int = Query(..., description="ID пользователя"),
    invite_key: Optional[str] = Query(None, description="Для приватных комнат"),
):
    """
    КОНТРАКТ:
    - Клиент подключается: /ws/rooms/{room}?user_id=1&invite_key=...
    - Сервер отвечает {"type":"joined","user_id":<you>,"room_slug":...}
    - На join других: {"type":"member.joined","user_id":<id>}
      На выход:        {"type":"member.left","user_id":<id>}
    - Сигналинг:
        to-one: {"type":"offer","to":<user_id>,"sdp":...}
                {"type":"answer","to":<user_id>,"sdp":...}
                {"type":"ice","to":<user_id>,"candidate":{...}}
      Сервер пересылает адресату, добавляя {"from": <sender_id>}
    - Heartbeat: любое сообщение от клиента обновляет last_seen в БД.
    """
    await websocket.accept()
    svc = await _participant_service()

    # проверим доступ и отметим участника активным
    try:
        m = await svc.join(room_slug=room_slug, user_id=user_id, invite_key=invite_key)
    except ValueError as e:
        await _safe_json_send(websocket, {"type": "error", "reason": str(e)})
        await _safe_close(websocket, status.WS_1008_POLICY_VIOLATION)
        return

    # регистрируем в хабе
    await HUB.join(room_slug, user_id, websocket)

    # подтвердим подключение клиенту
    await _safe_json_send(websocket, {
        "type": "joined",
        "room_slug": room_slug,
        "user_id": user_id,
    })

    # разошлём всем, что участник вошёл
    await HUB.broadcast(room_slug, {
        "type": "member.joined",
        "user_id": user_id,
    }, exclude={user_id})

    try:
        while True:
            raw = await websocket.receive_text()
            # любое сообщение = heartbeat
            await svc.heartbeat(room_slug=room_slug, user_id=user_id)

            try:
                msg = json.loads(raw)
                if not isinstance(msg, dict) or "type" not in msg:
                    raise ValueError("bad_payload")
            except Exception:
                await _safe_json_send(websocket, {"type": "error", "reason": "bad_json"})
                continue

            mtype = msg.get("type")

            # сигнальные сообщения to-one
            if mtype in ("offer", "answer", "ice"):
                to_uid = msg.get("to")
                if not isinstance(to_uid, int):
                    await _safe_json_send(websocket, {"type": "error", "reason": "missing_to"})
                    continue
                payload: Dict[str, Any] = {k: v for k, v in msg.items() if k not in ("type", "to")}
                payload.update({"type": mtype, "from": user_id})
                await HUB.send_to(room_slug, to_uid, payload)
                continue

            # мягкий leave по запросу клиента
            if mtype == "leave":
                break

            # можно расширять: mute/kick/raise-hand и т.п.
                # else: ignore

    except (WebSocketDisconnect, SWebSocketDisconnect):
        pass
    finally:
        # снять с онлайна, известить остальных
        await svc.leave(room_slug=room_slug, user_id=user_id)
        await HUB.leave(room_slug, user_id)
        await HUB.broadcast(room_slug, {
            "type": "member.left",
            "user_id": user_id,
        })

        await _safe_close(websocket, status.WS_1000_NORMAL_CLOSURE)

async def _safe_json_send(ws: WebSocket, data: dict) -> None:
    if ws.client_state == WebSocketState.CONNECTED:
        await ws.send_text(json.dumps(data, ensure_ascii=False))

async def _safe_close(ws: WebSocket, code: int) -> None:
    if ws.client_state == WebSocketState.CONNECTED:
        await ws.close(code=code)
