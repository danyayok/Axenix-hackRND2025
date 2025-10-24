from fastapi import APIRouter, Depends, HTTPException
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.repositories.membership_repo import MembershipRepository
from app.repositories.room_repo import RoomRepository
from app.repositories.user_repo import UserRepository
from app.services.participants import ParticipantService
from app.schemas.membership import (
    ParticipantJoinIn,
    ParticipantLeaveIn,
    ParticipantHeartbeatIn,
    ParticipantOut,
    ParticipantListOut,
)

router = APIRouter()

def _svc(db: AsyncSession) -> ParticipantService:
    return ParticipantService(
        MembershipRepository(db),
        RoomRepository(db),
        UserRepository(db),
    )

@router.post("/join", response_model=ParticipantOut, status_code=HTTP_201_CREATED)
async def join(payload: ParticipantJoinIn, db: AsyncSession = Depends(get_db)) -> ParticipantOut:
    try:
        m = await _svc(db).join(room_slug=payload.room_slug, user_id=payload.user_id, invite_key=payload.invite_key)
    except ValueError as e:
        msg = str(e)
        if msg == "room_not_found":
            raise HTTPException(HTTP_404_NOT_FOUND, "Room not found")
        if msg == "user_not_found":
            raise HTTPException(HTTP_404_NOT_FOUND, "User not found")
        if msg == "invite_required_or_invalid":
            raise HTTPException(HTTP_400_BAD_REQUEST, "Invite required or invalid")
        raise
    from app.services.participants import ONLINE_TTL_SECONDS
    from datetime import datetime, timedelta
    is_online = (datetime.utcnow() - m.last_seen) <= timedelta(seconds=ONLINE_TTL_SECONDS)
    return ParticipantOut(
        membership_id=m.id,
        room_slug=payload.room_slug,
        user_id=m.user_id,
        role=m.role,
        status=m.status,
        last_seen=m.last_seen,
        is_online=is_online,
    )

@router.post("/leave", response_model=ParticipantOut)
async def leave(payload: ParticipantLeaveIn, db: AsyncSession = Depends(get_db)) -> ParticipantOut:
    m = await _svc(db).leave(room_slug=payload.room_slug, user_id=payload.user_id)
    if not m:
        raise HTTPException(HTTP_404_NOT_FOUND, "Not found or already left")
    from app.services.participants import ONLINE_TTL_SECONDS
    from datetime import datetime, timedelta
    is_online = (datetime.utcnow() - m.last_seen) <= timedelta(seconds=ONLINE_TTL_SECONDS)
    return ParticipantOut(
        membership_id=m.id,
        room_slug=payload.room_slug,
        user_id=m.user_id,
        role=m.role,
        status=m.status,
        last_seen=m.last_seen,
        is_online=is_online,
    )

@router.post("/heartbeat", response_model=ParticipantOut)
async def heartbeat(payload: ParticipantHeartbeatIn, db: AsyncSession = Depends(get_db)) -> ParticipantOut:
    m = await _svc(db).heartbeat(room_slug=payload.room_slug, user_id=payload.user_id)
    if not m:
        raise HTTPException(HTTP_404_NOT_FOUND, "Active membership not found")
    from app.services.participants import ONLINE_TTL_SECONDS
    from datetime import datetime, timedelta
    is_online = (datetime.utcnow() - m.last_seen) <= timedelta(seconds=ONLINE_TTL_SECONDS)
    return ParticipantOut(
        membership_id=m.id,
        room_slug=payload.room_slug,
        user_id=m.user_id,
        role=m.role,
        status=m.status,
        last_seen=m.last_seen,
        is_online=is_online,
    )

@router.get("/{room_slug}", response_model=ParticipantListOut)
async def list_participants(room_slug: str, db: AsyncSession = Depends(get_db)) -> ParticipantListOut:
    try:
        items = await _svc(db).list(room_slug=room_slug)
    except ValueError:
        raise HTTPException(HTTP_404_NOT_FOUND, "Room not found")
    return ParticipantListOut(participants=[
        ParticipantOut(**i) for i in items
    ])
