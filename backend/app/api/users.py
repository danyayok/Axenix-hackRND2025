from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_404_NOT_FOUND
from pathlib import Path
from app.core.security import get_password_hash, verify_password
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
        password_hash = get_password_hash(payload.password)

    # Создаем пользователя
    user = await repo.create(
        nickname=payload.nickname,
        avatar_url=payload.avatar_url,
        email=payload.email,
        password_hash=password_hash
    )

    if payload.public_key_pem:
        user.public_key_pem = payload.public_key_pem

    await db.commit()
    await db.refresh(user)

    # Преобразуем SQLAlchemy модель в Pydantic модель
    return UserOut(
        id=user.id,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        public_key_pem=user.public_key_pem,
        email=user.email
    )


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    # Преобразуем SQLAlchemy модель в Pydantic модель
    return UserOut(
        id=user.id,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        public_key_pem=user.public_key_pem,
        email=user.email
    )


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(user_id: int, payload: UserUpdate, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    if payload.nickname is not None:
        user.nickname = payload.nickname
    if payload.avatar_url is not None:
        user.avatar_url = payload.avatar_url
    if payload.public_key_pem is not None:
        user.public_key_pem = payload.public_key_pem
    if payload.email is not None:
        user.email = payload.email

    await db.commit()
    await db.refresh(user)

    # Преобразуем SQLAlchemy модель в Pydantic модель
    return UserOut(
        id=user.id,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        public_key_pem=user.public_key_pem,
        email=user.email
    )


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
    await db.commit()
    await db.refresh(user)

    # Исправляем Pydantic валидацию - создаем UserOut явно
    return UserOut(
        id=user.id,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        public_key_pem=user.public_key_pem,
        email=user.email
    )


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    # Удаляем пользователя
    await db.delete(user)
    await db.commit()

    return {"message": "User deleted successfully"}


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/{user_id}/change-password")
async def change_password(
        user_id: int,
        payload: ChangePasswordRequest,
        db: AsyncSession = Depends(get_db)
):
    repo = UserRepository(db)
    user = await repo.get(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    if not user.password_hash or not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(400, "Current password is incorrect")

    user.password_hash = get_password_hash(payload.new_password)

    await db.commit()
    await db.refresh(user)

    return {"message": "Password changed successfully"}