from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from starlette.status import HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
import shutil

from app.api.deps import get_db
from app.repositories.room_repo import RoomRepository
from app.repositories.membership_repo import MembershipRepository

router = APIRouter()

COVERS_DIR = Path("static/covers")

async def _ensure_admin(db: AsyncSession, room_slug: str, actor_user_id: int):
    rrepo = RoomRepository(db); mrepo = MembershipRepository(db)
    room = await rrepo.get_by_slug(room_slug)
    if not room:
        raise HTTPException(HTTP_404_NOT_FOUND, "Room not found")
    m = await mrepo.get_active(room_id=room.id, user_id=actor_user_id)
    role = m.role if m else "guest"
    if role not in ("owner", "admin"):
        raise HTTPException(HTTP_403_FORBIDDEN, "Admin/Owner required")
    return room

def _cover_path(slug: str) -> Path | None:
    COVERS_DIR.mkdir(parents=True, exist_ok=True)
    for p in COVERS_DIR.glob(f"{slug}.*"):
        return p
    return None

@router.post("/{room_slug}/upload")
async def upload_cover(room_slug: str, actor_user_id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    room = await _ensure_admin(db, room_slug, actor_user_id)
    COVERS_DIR.mkdir(parents=True, exist_ok=True)
    # удалим старую
    old = _cover_path(room.slug)
    if old and old.exists():
        try: old.unlink()
        except Exception: pass
    # сохраним новую
    ext = Path(file.filename).suffix or ".jpg"
    dest = COVERS_DIR / f"{room.slug}{ext}"
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    return {"cover_url": f"/static/covers/{dest.name}"}

@router.get("/{room_slug}")
async def get_cover(room_slug: str):
    p = _cover_path(room_slug)
    if not p:
        raise HTTPException(HTTP_404_NOT_FOUND, "No cover")
    return {"cover_url": f"/static/covers/{p.name}"}

@router.delete("/{room_slug}")
async def delete_cover(room_slug: str, actor_user_id: int, db: AsyncSession = Depends(get_db)):
    room = await _ensure_admin(db, room_slug, actor_user_id)
    p = _cover_path(room.slug)
    if p and p.exists():
        p.unlink()
    return {"ok": True}
