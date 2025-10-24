from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_404_NOT_FOUND
from typing import Optional

from app.api.deps import get_db
from app.repositories.message_repo import MessageRepository
from app.repositories.room_repo import RoomRepository
from app.repositories.user_repo import UserRepository
from app.services.chat import ChatService
from app.schemas.message import ChatHistoryOut, ChatMessageOut

router = APIRouter()

def _svc(db: AsyncSession) -> ChatService:
    return ChatService(MessageRepository(db), RoomRepository(db), UserRepository(db))

@router.get("/{room_slug}", response_model=ChatHistoryOut)
async def get_history(
    room_slug: str,
    limit: int = Query(50, ge=1, le=200),
    before_id: Optional[int] = Query(None, description="paginate backward"),
    db: AsyncSession = Depends(get_db),
) -> ChatHistoryOut:
    try:
        items, has_more = await _svc(db).history(room_slug=room_slug, limit=limit, before_id=before_id)
    except ValueError:
        raise HTTPException(HTTP_404_NOT_FOUND, "Room not found")

    out = [
        ChatMessageOut(
            id=m.id,
            room_slug=room_slug,
            user_id=m.user_id,
            text=m.text,
            created_at=m.created_at,
        ) for m in items
    ]
    next_before_id = out[0].id if has_more and out else None
    return ChatHistoryOut(items=out, has_more=has_more, next_before_id=next_before_id)
