from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories.room_repo import RoomRepository
from app.repositories.membership_repo import MembershipRepository
from app.repositories.user_repo import UserRepository
from app.repositories.crypto_repo import CryptoRepository
from app.services.crypto import CryptoService

router = APIRouter()

def _svc(db: AsyncSession) -> CryptoService:
    return CryptoService(RoomRepository(db), MembershipRepository(db), UserRepository(db), CryptoRepository(db))

@router.post("/{room_slug}/init")
async def init_room_key(room_slug: str, actor_user_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    try:
        res = await _svc(db).init_room_key(room_slug=room_slug, actor_user_id=actor_user_id)
        return res
    except ValueError as e:
        if str(e) == "forbidden":
            raise HTTPException(HTTP_403_FORBIDDEN, "Owner/Admin required")
        raise HTTPException(HTTP_404_NOT_FOUND, str(e))

@router.get("/{room_slug}/my_key")
async def get_my_wrapped_key(room_slug: str, user_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    res = await _svc(db).get_my_wrapped_key(room_slug=room_slug, user_id=user_id)
    if not res:
        raise HTTPException(HTTP_404_NOT_FOUND, "No key for this user/room")
    return res
