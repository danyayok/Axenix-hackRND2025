from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.status import HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories.room_repo import RoomRepository
from app.repositories.membership_repo import MembershipRepository
from app.schemas.moderation import TargetUserIn, ForceMuteIn, RoleOut, ForceMuteOut, KickOut, SpeakIn, SpeakOut, ForceVideoIn, ForceVideoOut
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
    if not (role == "owner" or (room.created_by is not None and str(room.created_by) == str(actor_user_id)) or role == "admin"):
        # разрешим и admin, и owner
        raise HTTPException(HTTP_403_FORBIDDEN, "Admin/Owner rights required")

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

# NEW: права на выступление
@router.post("/{room_slug}/speak", response_model=SpeakOut)
async def set_speak(room_slug: str, payload: SpeakIn,
                    actor_user_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    await _ensure_owner(db, room_slug, actor_user_id)
    res = await _svc(db).set_speaker(room_slug, payload.user_id, payload.can_speak)
    await db.commit()
    await HUB.broadcast(room_slug, {"type":"speak.changed","user_id":res["user_id"],"can_speak":res["can_speak"]})
    return SpeakOut(**res)

# NEW: принудительное выключение/разрешение видео
@router.post("/{room_slug}/force_video", response_model=ForceVideoOut)
async def force_video(room_slug: str, payload: ForceVideoIn,
                      actor_user_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    await _ensure_owner(db, room_slug, actor_user_id)
    res = await _svc(db).set_video_off(room_slug, payload.user_id, payload.video_off)
    await db.commit()
    await HUB.broadcast(room_slug, {"type":"media.video_forced","user_id":res["user_id"],"admin_video_off":res["admin_video_off"]})
    return ForceVideoOut(**res)
