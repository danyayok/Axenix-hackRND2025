from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_404_NOT_FOUND
from pathlib import Path
import shutil
import bcrypt
from typing import Optional

from app.api.deps import get_db
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate, UserUpdate, UserOut

router = APIRouter()


# app/api/users.py
@router.post("", response_model=UserOut)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)

    # Если указан email, проверяем уникальность
    if payload.email:
        existing_user = await repo.get_by_email(payload.email)
        if existing_user:
            raise HTTPException(400, "Email already registered")

    # Хешируем пароль если указан
    password_hash = None
    if payload.password:
        password_hash = bcrypt.hashpw(payload.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Создаем пользователя через СУЩЕСТВУЮЩИЙ метод
    user = await repo.create(
        nickname=payload.nickname,
        avatar_url=payload.avatar_url,
        email=payload.email,
        password_hash=password_hash
    )

    if payload.public_key_pem:
        user.public_key_pem = payload.public_key_pem

    await db.flush()
    await db.refresh(user)
    return UserOut.model_validate(user)

@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get(user_id)
    if not user:
        raise HTTPException(HTTP_404_NOT_FOUND, "User not found")
    return UserOut.model_validate(user)

@router.patch("/{user_id}", response_model=UserOut)
async def update_user(user_id: int, payload: UserUpdate, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get(user_id)
    if not user:
        raise HTTPException(HTTP_404_NOT_FOUND, "User not found")

    if payload.nickname is not None:
        user.nickname = payload.nickname
    if payload.avatar_url is not None:
        user.avatar_url = payload.avatar_url
    if payload.public_key_pem is not None:  # NEW
        user.public_key_pem = payload.public_key_pem

    await db.flush()
    await db.refresh(user)
    return UserOut.model_validate(user)

# загрузка аватара (если у тебя этот эндпоинт уже есть — оставь свой вариант)
@router.post("/{user_id}/avatar", response_model=UserOut)
async def upload_avatar(user_id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get(user_id)
    if not user:
        raise HTTPException(HTTP_404_NOT_FOUND, "User not found")

    Path("static/avatars").mkdir(parents=True, exist_ok=True)
    dest = Path("static/avatars") / f"user_{user_id}{Path(file.filename).suffix}"
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    user.avatar_url = f"/static/avatars/{dest.name}"
    await db.flush()
    await db.refresh(user)
    return UserOut.model_validate(user)
