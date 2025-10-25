# ws.py (улучшенная версия с метриками)
from typing import Optional, Any, Dict
import json
import time

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
from app.services.metrics import MetricsService

router = APIRouter()

# Глобальный экземпляр метрик для reuse между подключениями
_metrics_service = None


def get_metrics_service(db: AsyncSession) -> MetricsService:
    """Получить или создать сервис метрик"""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = MetricsService(
            room_repo=RoomRepository(db),
            user_repo=UserRepository(db),
            message_repo=MessageRepository(db),
            membership_repo=MembershipRepository(db)
        )
    return _metrics_service


@router.websocket("/ws/rooms/{room_slug}")
async def ws_room(
        websocket: WebSocket,
        room_slug: str,
        token: str = Query(..., description="JWT access token (guest)"),
        invite_key: Optional[str] = Query(None, description="Для приватных комнат"),
):
    connection_start_time = time.time()
    user_id = None

    await websocket.accept()

    try:
        user_id = get_user_id_from_token(token)
    except Exception as e:
        await _safe_json_send(websocket, {"type": "error", "reason": "invalid_token"})
        await _safe_close(websocket, status.WS_1008_POLICY_VIOLATION)
        return

    db: AsyncSession = SessionLocal()

    # Инициализация репозиториев и сервисов
    rrepo = RoomRepository(db)
    mrepo = MembershipRepository(db)
    erepo = EventRepository(db)
    urepo = UserRepository(db)
    msg_repo = MessageRepository(db)

    # Инициализация сервиса метрик
    metrics_service = get_metrics_service(db)

    svc_part = ParticipantService(mrepo, rrepo, urepo)
    svc_chat = ChatService(msg_repo, rrepo, urepo)
    svc_state = StateService(rrepo, mrepo)
    svc_media = MediaService(rrepo, mrepo)
    svc_sync = SyncService(rrepo, erepo)

    try:
        # JOIN
        try:
            membership = await svc_part.join(room_slug=room_slug, user_id=user_id, invite_key=invite_key)
            await db.commit()

            # Метрика: присоединение к комнате
            metrics_service.increment_join_count(room_slug)

            # Обновляем метрики участников
            room = await rrepo.get_by_slug(room_slug)
            if room:
                participants = await mrepo.list_by_room(room_id=room.id)
                online_count = sum(1 for p in participants if p.status == "active")
                metrics_service.update_room_participants(room_slug, online_count)

        except ValueError as e:
            error_type = f"join_error_{str(e)}"
            metrics_service.increment_errors(error_type)
            await _safe_json_send(websocket, {"type": "error", "reason": str(e)})
            await _safe_close(websocket, status.WS_1008_POLICY_VIOLATION)
            return

        # Успешное подключение
        await HUB.join(room_slug, user_id, websocket)
        await _safe_json_send(websocket, {
            "type": "joined",
            "room_slug": room_slug,
            "user_id": user_id,
            "connection_time_ms": int((time.time() - connection_start_time) * 1000)
        })

        # Отправка начального состояния
        snap = await svc_state.snapshot(room_slug)
        await _safe_json_send(websocket, {"type": "state.snapshot", **snap})

        next_seq = await svc_sync.next_seq()
        await _safe_json_send(websocket, {"type": "sync.info", "next_seq": next_seq})

        # Уведомление других участников
        await HUB.broadcast(room_slug, {"type": "member.joined", "user_id": user_id}, exclude={user_id})
        ev = await svc_sync.append(room_slug=room_slug, type_="member.joined", payload={"user_id": user_id})
        await db.commit()

        # Основной цикл обработки сообщений
        message_count = 0
        while True:
            raw = await websocket.receive_text()
            message_count += 1

            # Heartbeat для поддержания активности
            await svc_part.heartbeat(room_slug=room_slug, user_id=user_id)
            await db.commit()

            try:
                msg = json.loads(raw)
                if not isinstance(msg, dict) or "type" not in msg:
                    raise ValueError("bad_payload")
            except Exception as e:
                metrics_service.increment_errors("bad_json")
                await _safe_json_send(websocket, {"type": "error", "reason": "bad_json"})
                continue

            mtype = msg.get("type")

            # Метрика: WebSocket событие
            metrics_service.increment_ws_events(mtype)

            # Получение текущего состояния комнаты и пользователя
            room = await rrepo.get_by_slug(room_slug)
            if not room:
                await _safe_json_send(websocket, {"type": "error", "reason": "room_not_found"})
                continue

            membership = await mrepo.get_active(room_id=room.id, user_id=user_id)
            if not membership:
                await _safe_json_send(websocket, {"type": "error", "reason": "not_a_member"})
                continue

            role = membership.role
            mute_all = bool(room.mute_all)
            admin_muted = bool(membership.admin_muted)
            admin_video_off = bool(getattr(membership, "admin_video_off", False))
            can_speak = bool(getattr(membership, "can_speak", False))
            is_privileged = role in ("owner", "admin")

            # Проверка ограничений доступа
            if admin_muted and mtype in ("offer", "answer", "ice", "chat.message", "chat.message.enc"):
                await _safe_json_send(websocket, {"type": "error", "reason": "muted_by_admin"})
                continue

            if mute_all and not (is_privileged or can_speak):
                if mtype in ("offer", "answer", "ice", "chat.message", "chat.message.enc"):
                    await _safe_json_send(websocket, {"type": "error", "reason": "mute_all"})
                    continue

            # Обработка различных типов сообщений
            await _handle_websocket_message(
                mtype, msg, room_slug, user_id,
                is_privileged, metrics_service,
                svc_chat, svc_state, svc_media, svc_sync,
                db, HUB
            )

    except (WebSocketDisconnect, SWebSocketDisconnect):
        # Нормальное отключение
        metrics_service.increment_ws_events("disconnect_normal")
    except Exception as e:
        # Неожиданная ошибка
        error_type = f"unexpected_error_{type(e).__name__}"
        metrics_service.increment_errors(error_type)
        raise
    finally:
        # Cleanup при отключении
        await _cleanup_connection(
            room_slug, user_id, db,
            svc_part, svc_sync, HUB, metrics_service,
            connection_start_time, message_count if 'message_count' in locals() else 0
        )


async def _handle_websocket_message(
        mtype: str,
        msg: Dict[str, Any],
        room_slug: str,
        user_id: int,
        is_privileged: bool,
        metrics_service: MetricsService,
        svc_chat: ChatService,
        svc_state: StateService,
        svc_media: MediaService,
        svc_sync: SyncService,
        db: AsyncSession,
        hub
):
    """Обработка конкретных типов WebSocket сообщений"""

    # ---- SYNC subscribe ----
    if mtype == "sync.sub":
        after_seq = int(msg.get("after_seq", 0))
        limit = min(int(msg.get("limit", 200)), 500)  # Ограничение для безопасности
        items = await svc_sync.list_after(room_slug=room_slug, after_seq=after_seq, limit=limit)
        await _safe_json_send(hub.get_connection(room_slug, user_id), {"type": "sync.batch", "items": items})
        return

    # ---- WebRTC signaling ----
    if mtype in ("offer", "answer", "ice"):
        to_uid = msg.get("to")
        if not isinstance(to_uid, int):
            await _safe_json_send(hub.get_connection(room_slug, user_id), {"type": "error", "reason": "missing_to"})
            return

        payload: Dict[str, Any] = {k: v for k, v in msg.items() if k not in ("type", "to")}
        payload.update({"type": mtype, "from": user_id})
        await hub.send_to(room_slug, to_uid, payload)

        # Метрика для WebRTC событий
        if mtype == "offer":
            metrics_service.increment_ws_events("webrtc_offer")
        elif mtype == "answer":
            metrics_service.increment_ws_events("webrtc_answer")
        elif mtype == "ice":
            metrics_service.increment_ws_events("webrtc_ice")
        return

    # ---- chat (plaintext) ----
    if mtype == "chat.message":
        text = msg.get("text", "").strip()
        if not text:
            await _safe_json_send(hub.get_connection(room_slug, user_id), {"type": "error", "reason": "empty_message"})
            return

        try:
            saved = await svc_chat.send(room_slug=room_slug, user_id=user_id, text=text)
            await db.commit()

            # Метрика: отправка сообщения
            metrics_service.increment_message_count(room_slug, encrypted=False)

            # Синхронизация и broadcast
            ev = await svc_sync.append(
                room_slug=room_slug,
                type_="chat.message",
                payload={
                    "id": saved.id,
                    "room_slug": room_slug,
                    "user_id": user_id,
                    "text": saved.text,
                    "created_at": saved.created_at.isoformat() + "Z"
                }
            )
            await db.commit()

            await hub.broadcast(room_slug, {
                "type": "chat.message",
                "seq": ev.id,
                "id": saved.id,
                "room_slug": room_slug,
                "user_id": user_id,
                "text": saved.text,
                "created_at": saved.created_at.isoformat() + "Z"
            })

        except ValueError as e:
            metrics_service.increment_errors(f"chat_error_{str(e)}")
            await _safe_json_send(hub.get_connection(room_slug, user_id), {"type": "error", "reason": str(e)})
        return

    # ---- chat (encrypted) ----
    if mtype == "chat.message.enc":
        b64 = msg.get("ciphertext_b64", "").strip()
        if not b64:
            await _safe_json_send(hub.get_connection(room_slug, user_id),
                                  {"type": "error", "reason": "empty_ciphertext"})
            return

        algo = msg.get("algo", "AES-256-GCM")
        try:
            saved = await svc_chat.send_encrypted(room_slug=room_slug, user_id=user_id, b64_cipher=b64, algo=algo)
            await db.commit()

            ev = await svc_sync.append(
                room_slug=room_slug,
                type_="chat.message.enc",
                payload={
                    "id": saved.id,
                    "room_slug": room_slug,
                    "user_id": user_id,
                    "algo": saved.enc_algo,
                    "ciphertext_b64": saved.text,
                    "created_at": saved.created_at.isoformat() + "Z"
                }
            )
            await db.commit()

            await hub.broadcast(room_slug, {
                "type": "chat.message.enc",
                "seq": ev.id,
                "id": saved.id,
                "room_slug": room_slug,
                "user_id": user_id,
                "algo": saved.enc_algo,
                "ciphertext_b64": saved.text,
                "created_at": saved.created_at.isoformat() + "Z"
            })

            # Метрика: зашифрованное сообщение
            metrics_service.increment_message_count(room_slug, encrypted=True)

        except ValueError as e:
            metrics_service.increment_errors(f"chat_enc_error_{str(e)}")
            await _safe_json_send(hub.get_connection(room_slug, user_id), {"type": "error", "reason": str(e)})
        return

    # ---- typing indicator ----
    if mtype == "chat.typing":
        is_typing = bool(msg.get("is_typing", True))
        await hub.broadcast(room_slug, {
            "type": "chat.typing",
            "user_id": user_id,
            "is_typing": is_typing
        }, exclude={user_id})
        return

    # ---- state management (owner/admin only) ----
    if mtype == "state.set":
        if not is_privileged:
            await _safe_json_send(hub.get_connection(room_slug, user_id), {"type": "error", "reason": "forbidden"})
            return

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
            ev = await svc_sync.append(room_slug=room_slug, type_="state.changed", payload=latest)
            await db.commit()
            await hub.broadcast(room_slug, {"type": "state.changed", "seq": ev.id, **latest})
            metrics_service.increment_ws_events("state_changed")
        return

    # ---- media controls ----
    if mtype == "media.self":
        mic_muted = msg.get("mic_muted", None)
        cam_off = msg.get("cam_off", None)

        try:
            state = await svc_media.update_self(
                room_slug=room_slug,
                user_id=user_id,
                mic_muted=mic_muted,
                cam_off=cam_off
            )
            await db.commit()

            ev = await svc_sync.append(room_slug=room_slug, type_="media.updated", payload=state)
            await db.commit()

            await hub.broadcast(room_slug, {"type": "media.updated", "seq": ev.id, **state})

            # Обновление метрик медиа-стримов
            current_streams = len(hub.get_room_users(room_slug)) if hasattr(hub, 'get_room_users') else 0
            metrics_service.update_media_streams(room_slug, current_streams)
            metrics_service.increment_ws_events("media_updated")

        except ValueError as e:
            metrics_service.increment_errors(f"media_error_{str(e)}")
            await _safe_json_send(hub.get_connection(room_slug, user_id), {"type": "error", "reason": str(e)})
        return

    # ---- hand raising ----
    if mtype == "hand.raise":
        try:
            latest = await svc_state.set_hand(room_slug, user_id, True)
            await db.commit()

            ev = await svc_sync.append(room_slug=room_slug, type_="hand.raised", payload={"user_id": user_id, **latest})
            await db.commit()

            await hub.broadcast(room_slug, {"type": "hand.raised", "seq": ev.id, "user_id": user_id, **latest})
            metrics_service.increment_ws_events("hand_raised")

        except ValueError as e:
            metrics_service.increment_errors(f"hand_raise_error_{str(e)}")
        return

    if mtype == "hand.lower":
        try:
            latest = await svc_state.set_hand(room_slug, user_id, False)
            await db.commit()

            ev = await svc_sync.append(room_slug=room_slug, type_="hand.lowered",
                                       payload={"user_id": user_id, **latest})
            await db.commit()

            await hub.broadcast(room_slug, {"type": "hand.lowered", "seq": ev.id, "user_id": user_id, **latest})
            metrics_service.increment_ws_events("hand_lowered")

        except ValueError as e:
            metrics_service.increment_errors(f"hand_lower_error_{str(e)}")
        return

    # ---- recording controls (owner/admin only) ----
    if mtype == "record.start":
        if not is_privileged:
            await _safe_json_send(hub.get_connection(room_slug, user_id), {"type": "error", "reason": "forbidden"})
            return

        try:
            latest = await svc_state.set_recording(room_slug, True)
            await db.commit()

            ev = await svc_sync.append(room_slug=room_slug, type_="record.started",
                                       payload={"by_user": user_id, **latest})
            await db.commit()

            await hub.broadcast(room_slug, {"type": "record.started", "seq": ev.id, "by_user": user_id, **latest})
            metrics_service.increment_ws_events("record_started")

        except ValueError as e:
            metrics_service.increment_errors(f"record_start_error_{str(e)}")
        return

    if mtype == "record.stop":
        if not is_privileged:
            await _safe_json_send(hub.get_connection(room_slug, user_id), {"type": "error", "reason": "forbidden"})
            return

        try:
            latest = await svc_state.set_recording(room_slug, False)
            await db.commit()

            ev = await svc_sync.append(room_slug=room_slug, type_="record.stopped",
                                       payload={"by_user": user_id, **latest})
            await db.commit()

            await hub.broadcast(room_slug, {"type": "record.stopped", "seq": ev.id, "by_user": user_id, **latest})
            metrics_service.increment_ws_events("record_stopped")

        except ValueError as e:
            metrics_service.increment_errors(f"record_stop_error_{str(e)}")
        return

    # ---- graceful leave ----
    if mtype == "leave":
        # Выход будет обработан в основном цикле
        return

    # ---- unknown message type ----
    metrics_service.increment_errors(f"unknown_message_type_{mtype}")
    await _safe_json_send(hub.get_connection(room_slug, user_id), {
        "type": "error",
        "reason": f"unknown_message_type: {mtype}"
    })


async def _cleanup_connection(
        room_slug: str,
        user_id: int,
        db: AsyncSession,
        svc_part: ParticipantService,
        svc_sync: SyncService,
        hub,
        metrics_service: MetricsService,
        connection_start_time: float,
        message_count: int
):
    """Очистка ресурсов при отключении"""
    try:
        if user_id:
            # Выход из комнаты
            await svc_part.leave(room_slug=room_slug, user_id=user_id)
            await db.commit()

            # Выход из hub
            await hub.leave(room_slug, user_id)

            # Синхронизация события выхода
            ev = await svc_sync.append(room_slug=room_slug, type_="member.left", payload={"user_id": user_id})
            await db.commit()

            # Уведомление других участников
            await hub.broadcast(room_slug, {"type": "member.left", "seq": ev.id, "user_id": user_id})

            # Метрики отключения
            connection_duration = time.time() - connection_start_time
            metrics_service.increment_ws_events("member_left")
            metrics_service.record_response_time(connection_duration)

            # Обновление счетчика участников
            room_repo = RoomRepository(db)
            room = await room_repo.get_by_slug(room_slug)
            if room:
                mrepo = MembershipRepository(db)
                participants = await mrepo.list_by_room(room_id=room.id)
                online_count = sum(1 for p in participants if p.status == "active")
                metrics_service.update_room_participants(room_slug, online_count)

    except Exception as e:
        metrics_service.increment_errors(f"cleanup_error_{type(e).__name__}")
    finally:
        await db.close()


async def _safe_json_send(ws: WebSocket, data: dict) -> None:
    """Безопасная отправка JSON через WebSocket"""
    if ws and ws.client_state == WebSocketState.CONNECTED:
        try:
            await ws.send_json(data)
        except Exception:
            # Игнорируем ошибки отправки при разорванном соединении
            pass


async def _safe_close(ws: WebSocket, code: int) -> None:
    """Безопасное закрытие WebSocket соединения"""
    if ws and ws.client_state == WebSocketState.CONNECTED:
        try:
            await ws.close(code=code)
        except Exception:
            # Игнорируем ошибки закрытия
            pass