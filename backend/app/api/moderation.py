from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.status import HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories.room_repo import RoomRepository
from app.repositories.membership_repo import MembershipRepository
from app.schemas.moderation import TargetUserIn, ForceMuteIn, RoleOut, ForceMuteOut, KickOut
from app.services.moderation import ModerationService
from app.services.ws_hub import HUB

router = APIRouter()

def _svc(db: AsyncSession) -> ModerationService:
    return ModerationService(RoomRepository(db), MembershipRepository(db))

async def _ensure_owner(db: AsyncSession, room_slug: str, actor_user_id: int):
    rrepo = RoomRepository(db); mrepo = MembershipRepository(db)
    room = await rrepo.get_by_slug(room_slug)
    if not room:
        raise HTTPException(HTTP_404_NOT_FOUND, "Room not found")
    m = await mrepo.get_active(room_id=room.id, user_id=actor_user_id)
    role = m.role if m else None
    if not (role == "owner" or (room.created_by is not None and str(room.created_by) == str(actor_user_id))):
        raise HTTPException(HTTP_403_FORBIDDEN, "Owner rights required")

@router.post("/{room_slug}/promote_admin", response_model=RoleOut)
async def promote_admin(room_slug: str, payload: TargetUserIn,
                        actor_user_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    await _ensure_owner(db, room_slug, actor_user_id)
    res = await _svc(db).promote(room_slug, payload.user_id)
    await db.commit()
    await HUB.broadcast(room_slug, {"type":"role.changed","user_id":res["user_id"],"role":res["role"]})
    return RoleOut(**res)

@router.post("/{room_slug}/demote_admin", response_model=RoleOut)
async def demote_admin(room_slug: str, payload: TargetUserIn,
                       actor_user_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    await _ensure_owner(db, room_slug, actor_user_id)
    res = await _svc(db).demote(room_slug, payload.user_id)
    await db.commit()
    await HUB.broadcast(room_slug, {"type":"role.changed","user_id":res["user_id"],"role":res["role"]})
    return RoleOut(**res)

@router.post("/{room_slug}/force_mute", response_model=ForceMuteOut)
async def force_mute(room_slug: str, payload: ForceMuteIn,
                     actor_user_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    await _ensure_owner(db, room_slug, actor_user_id)
    res = await _svc(db).force_mute(room_slug, payload.user_id, payload.muted)
    await db.commit()
    await HUB.broadcast(room_slug, {"type":"media.forced","user_id":res["user_id"],"admin_muted":res["admin_muted"]})
    return ForceMuteOut(**res)

@router.post("/{room_slug}/kick", response_model=KickOut)
async def kick(room_slug: str, payload: TargetUserIn,
               actor_user_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    await _ensure_owner(db, room_slug, actor_user_id)
    res = await _svc(db).kick(room_slug, payload.user_id)
    await db.commit()
    await HUB.broadcast(room_slug, {"type":"member.kicked","user_id":res["user_id"]})
    return KickOut(**res)
