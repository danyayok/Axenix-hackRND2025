from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.status import HTTP_404_NOT_FOUND
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories.event_repo import EventRepository
from app.repositories.room_repo import RoomRepository
from app.services.sync import SyncService

router = APIRouter()

@router.get("/{room_slug}")
async def get_events(
    room_slug: str,
    after_seq: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    svc = SyncService(RoomRepository(db), EventRepository(db))
    try:
        items = await svc.list_after(room_slug=room_slug, after_seq=after_seq, limit=limit)
        return {"items": items}
    except ValueError as e:
        raise HTTPException(HTTP_404_NOT_FOUND, str(e))
