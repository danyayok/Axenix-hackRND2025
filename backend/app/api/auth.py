from fastapi import APIRouter, HTTPException, Depends
from starlette.status import HTTP_404_NOT_FOUND, HTTP_401_UNAUTHORIZED
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.repositories.user_repo import UserRepository
from app.core.security import create_access_token, verify_password
from app.core.config import settings
from app.schemas.auth import GuestTokenIn, TokenOut, LoginRequest
from app.schemas.user import UserOut  # используем существующую схему


router = APIRouter()


@router.post("/token/guest", response_model=TokenOut)
async def guest_token(payload: GuestTokenIn, db: AsyncSession = Depends(get_db)) -> TokenOut:
    # выдаём токен существующему пользователю
    user = await UserRepository(db).get(payload.user_id)
    if not user:
        raise HTTPException(HTTP_404_NOT_FOUND, "User not found")

    # Используем твою функцию create_access_token
    token = create_access_token(user_id=payload.user_id)

    return TokenOut(
        access_token=token,
        token_type="bearer",
        expires_in=settings.jwt_ttl_seconds
    )

# ДОБАВЛЯЕМ ЭНДПОИНТ ЛОГИНА
@router.post("/login", response_model=TokenOut)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenOut:
    repo = UserRepository(db)

    # Ищем пользователя по email
    user = await repo.get_by_email(payload.email)
    if not user or not user.password_hash:
        raise HTTPException(HTTP_401_UNAUTHORIZED, "Invalid credentials")

    # Проверяем пароль
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(HTTP_401_UNAUTHORIZED, "Invalid credentials")

    # Создаем токен
    token = create_access_token(user_id=user.id)

    return TokenOut(
        access_token=token,
        token_type="bearer",
        expires_in=settings.jwt_ttl_seconds,
        user_id=user.id,  # Добавляем ID пользователя
        user=UserOut(     # Добавляем данные пользователя
            id=user.id,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            public_key_pem=user.public_key_pem,
            email=user.email
        )
    )