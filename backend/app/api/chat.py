from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.status import HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories.room_repo import RoomRepository
from app.repositories.membership_repo import MembershipRepository
from app.repositories.message_repo import MessageRepository
from app.repositories.user_repo import UserRepository
from app.services.chat import ChatService
from app.schemas.chat import MessageOut, HistoryOut
from app.schemas.message import MessageCreate

router = APIRouter()

def _svc(db: AsyncSession) -> ChatService:
    return ChatService(MessageRepository(db), RoomRepository(db), UserRepository(db))

@router.get("/{room_slug}", response_model=HistoryOut)
async def get_history(
    room_slug: str,
    limit: int = Query(50, ge=1, le=200),
    before_id: int | None = Query(None, ge=1),
    db: AsyncSession = Depends(get_db),
) -> HistoryOut:
    try:
        items = await _svc(db).history(room_slug=room_slug, limit=limit, before_id=before_id)
        return HistoryOut(items=[MessageOut.model_validate(m) for m in items])
    except ValueError as e:
        raise HTTPException(HTTP_404_NOT_FOUND, str(e))

@router.delete("/{room_slug}/{message_id}")
async def delete_message(
    room_slug: str,
    message_id: int,
    actor_user_id: int = Query(..., description="Owner/Admin ID"),
    db: AsyncSession = Depends(get_db),
):
    # только owner/admin
    rrepo = RoomRepository(db)
    mrepo = MembershipRepository(db)
    room = await rrepo.get_by_slug(room_slug)
    if not room:
        raise HTTPException(HTTP_404_NOT_FOUND, "Room not found")
    m = await mrepo.get_active(room_id=room.id, user_id=actor_user_id)
    role = m.role if m else "guest"
    if role not in ("owner", "admin"):
        raise HTTPException(HTTP_403_FORBIDDEN, "Admin required")

    ok = await ChatService(MessageRepository(db), rrepo, UserRepository(db)).delete(room_slug=room_slug, message_id=message_id)
    return {"ok": bool(ok)}


@router.post("/{room_slug}")
async def send_message(
        room_slug: str,
        payload: MessageCreate,
        db: AsyncSession = Depends(get_db)
):
    # Находим комнату
    room_repo = RoomRepository(db)
    room = await room_repo.get_by_slug(room_slug)
    if not room:
        raise HTTPException(404, "Room not found")

    # Проверяем, что пользователь является участником
    participant_repo = ParticipantRepository(db)
    participant = await participant_repo.get_participant(room.id, payload.user_id)
    if not participant:
        raise HTTPException(403, "User is not a participant of this room")

    # Сохраняем сообщение
    message_repo = MessageRepository(db)
    message = await message_repo.create(
        room_id=room.id,
        user_id=payload.user_id,
        text=payload.text
    )

    await db.commit()
    await db.refresh(message)

    return MessageOut.from_orm(message)


@router.get("/{room_slug}/recent")
async def get_recent_messages(
        room_slug: str,
        limit: int = Query(20, ge=1, le=100),
        db: AsyncSession = Depends(get_db)
):
    """Получить последние сообщения (новый эндпоинт)"""
    room_repo = RoomRepository(db)
    room = await room_repo.get_by_slug(room_slug)
    if not room:
        raise HTTPException(404, "Room not found")

    message_repo = MessageRepository(db)
    messages = await message_repo.get_recent_room_messages(room.id, limit)

    return HistoryOut(items=messages)


@router.get("/{room_slug}/count")
async def get_message_count(
        room_slug: str,
        db: AsyncSession = Depends(get_db)
):
    """Получить количество сообщений в комнате (новый эндпоинт)"""
    room_repo = RoomRepository(db)
    room = await room_repo.get_by_slug(room_slug)
    if not room:
        raise HTTPException(404, "Room not found")

    message_repo = MessageRepository(db)
    count = await message_repo.count_room_messages(room.id)

    return {"room_slug": room_slug, "message_count": count}