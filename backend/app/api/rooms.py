from typing import List
from fastapi import APIRouter, Depends, HTTPException
from starlette.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED

from app.api.deps import get_room_service
from app.services.rooms import RoomService
from app.schemas.room import (
    RoomCreate,
    RoomOut,
    RoomListItem,
    RoomExistsOut,
    RoomJoinByInviteIn,
)

router = APIRouter()

@router.post("", response_model=RoomOut, status_code=HTTP_201_CREATED)
async def create_room(payload: RoomCreate, svc: RoomService = Depends(get_room_service)) -> RoomOut:
    room = await svc.create_room(
        title=payload.title,
        is_private=payload.is_private,
        create_invite=payload.create_invite,
        created_by=payload.created_by,
    )
    return RoomOut(
        id=room.id,
        slug=room.slug,
        title=room.title,
        is_private=room.is_private,
        invite_key=room.invite_key,
        invite_url=svc.make_invite_url(room),
    )

@router.get("", response_model=List[RoomListItem])
async def list_rooms(svc: RoomService = Depends(get_room_service)) -> List[RoomListItem]:
    rooms = await svc.repo.list()
    return [
        RoomListItem(
            id=r.id,
            slug=r.slug,
            title=r.title,
            is_private=r.is_private,
            invite_key=r.invite_key,
            invite_url=svc.make_invite_url(r),
        )
        for r in rooms
    ]

@router.get("/{slug}", response_model=RoomOut)
async def get_room(slug: str, svc: RoomService = Depends(get_room_service)) -> RoomOut:
    room = await svc.repo.get_by_slug(slug)
    if not room:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Room not found")
    return RoomOut(
        id=room.id,
        slug=room.slug,
        title=room.title,
        is_private=room.is_private,
        invite_key=room.invite_key,
        invite_url=svc.make_invite_url(room),
    )

@router.get("/{slug}/exists", response_model=RoomExistsOut)
async def room_exists(slug: str, svc: RoomService = Depends(get_room_service)) -> RoomExistsOut:
    return RoomExistsOut(exists=await svc.repo.slug_exists(slug))

@router.post("/join/by-invite", response_model=RoomOut)
async def join_by_invite(payload: RoomJoinByInviteIn, svc: RoomService = Depends(get_room_service)) -> RoomOut:
    room = await svc.repo.get_by_invite_key(payload.invite_key)
    if not room:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Invalid invite key")
    return RoomOut(
        id=room.id,
        slug=room.slug,
        title=room.title,
        is_private=room.is_private,
        invite_key=room.invite_key,
        invite_url=svc.make_invite_url(room),
    )
