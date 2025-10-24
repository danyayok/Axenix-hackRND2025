from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories.user_repo import UserRepository
from app.services.users import UserService
from app.schemas.user import UserCreate, UserOut

# NEW (для аватарок)
from PIL import Image
from uuid import uuid4
import os

router = APIRouter()

def _svc(db: AsyncSession) -> UserService:
    return UserService(UserRepository(db))

@router.post("", response_model=UserOut, status_code=HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> UserOut:
    u = await _svc(db).create_user(nickname=payload.nickname, avatar_url=payload.avatar_url)
    return UserOut.model_validate(u)

# Загрузка аватарки (JPEG/PNG/WebP → сохраняем как JPEG)
@router.post("/{user_id}/avatar", response_model=UserOut)
async def upload_avatar(
    user_id: int,
    file: UploadFile = File(..., description="image/jpeg | image/png | image/webp"),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    user = await UserRepository(db).get(user_id)
    if not user:
        raise HTTPException(HTTP_404_NOT_FOUND, "User not found")

    ctype = (file.content_type or "").lower()
    if ctype not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(HTTP_400_BAD_REQUEST, "Only JPEG, PNG or WebP allowed")

    # если клиент прислал размер — проверим (~2 МБ)
    if getattr(file, "size", None) and file.size > 2 * 1024 * 1024:
        raise HTTPException(HTTP_400_BAD_REQUEST, "File too large")

    # читаем и безопасно перекодируем
    try:
        img = Image.open(file.file).convert("RGB")
    except Exception:
        raise HTTPException(HTTP_400_BAD_REQUEST, "Invalid image")

    user_dir = os.path.join("static", "avatars", str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    fname = f"{uuid4().hex}.jpg"
    fpath = os.path.join(user_dir, fname)

    # сохраняем JPEG без EXIF, умеренно сжимаем
    img.save(fpath, format="JPEG", quality=85, optimize=True)

    public_path = f"/static/avatars/{user_id}/{fname}"
    updated = await UserRepository(db).update_avatar_url(user_id, public_path)
    if not updated:
        raise HTTPException(HTTP_404_NOT_FOUND, "User not found")

    return UserOut.model_validate(updated)
