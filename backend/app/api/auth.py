from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_404_NOT_FOUND
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from fastapi import Depends
from app.repositories.user_repo import UserRepository
from app.core.security import create_access_token
from app.core.config import settings
from app.schemas.auth import GuestTokenIn, TokenOut

router = APIRouter()

@router.post("/token/guest", response_model=TokenOut)
async def guest_token(payload: GuestTokenIn, db: AsyncSession = Depends(get_db)) -> TokenOut:
    # выдаём токен существующему пользователю
    user = await UserRepository(db).get(payload.user_id)
    if not user:
        raise HTTPException(HTTP_404_NOT_FOUND, "User not found")
    token = create_access_token(user_id=payload.user_id)
    return TokenOut(access_token=token, expires_in=settings.jwt_ttl_seconds)
