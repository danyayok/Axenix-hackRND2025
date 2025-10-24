from fastapi import APIRouter, Depends, HTTPException
from starlette.status import HTTP_404_NOT_FOUND
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories.room_repo import RoomRepository
from app.repositories.membership_repo import MembershipRepository
from app.services.state import StateService
from app.schemas.state import RoomStateOut, SetTopicIn, ToggleIn

router = APIRouter()

def _svc(db: AsyncSession) -> StateService:
    return StateService(RoomRepository(db), MembershipRepository(db))

@router.get("/{room_slug}", response_model=RoomStateOut)
async def get_state(room_slug: str, db: AsyncSession = Depends(get_db)) -> RoomStateOut:
    try:
        snap = await _svc(db).snapshot(room_slug)
    except ValueError:
        raise HTTPException(HTTP_404_NOT_FOUND, "Room not found")
    return RoomStateOut(**snap)

@router.post("/{room_slug}/topic", response_model=RoomStateOut)
async def set_topic(room_slug: str, payload: SetTopicIn, db: AsyncSession = Depends(get_db)) -> RoomStateOut:
    try:
        snap = await _svc(db).set_topic(room_slug, payload.topic)
    except ValueError:
        raise HTTPException(HTTP_404_NOT_FOUND, "Room not found")
    return RoomStateOut(**snap)

@router.post("/{room_slug}/lock", response_model=RoomStateOut)
async def set_lock(room_slug: str, payload: ToggleIn, db: AsyncSession = Depends(get_db)) -> RoomStateOut:
    try:
        snap = await _svc(db).set_locked(room_slug, payload.value)
    except ValueError:
        raise HTTPException(HTTP_404_NOT_FOUND, "Room not found")
    return RoomStateOut(**snap)

@router.post("/{room_slug}/mute_all", response_model=RoomStateOut)
async def set_mute_all(room_slug: str, payload: ToggleIn, db: AsyncSession = Depends(get_db)) -> RoomStateOut:
    try:
        snap = await _svc(db).set_mute_all(room_slug, payload.value)
    except ValueError:
        raise HTTPException(HTTP_404_NOT_FOUND, "Room not found")
    return RoomStateOut(**snap)
