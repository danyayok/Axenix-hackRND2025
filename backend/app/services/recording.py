from pathlib import Path
import shutil
from typing import Sequence, Optional
from app.repositories.room_repo import RoomRepository
from app.repositories.recording_repo import RecordingRepository
from app.repositories.membership_repo import MembershipRepository

class RecordingService:
    def __init__(self, rrepo: RoomRepository, mrepo: MembershipRepository, rec_repo: RecordingRepository):
        self.rrepo = rrepo; self.mrepo = mrepo; self.rec_repo = rec_repo
        self.base_dir = Path("static/records")

    async def _room(self, slug: str):
        room = await self.rrepo.get_by_slug(slug)
        if not room: raise ValueError("room_not_found")
        return room

    async def can_upload(self, room_id: int, user_id: int) -> bool:
        m = await self.mrepo.get_active(room_id=room_id, user_id=user_id)
        return bool(m)  # любой активный участник может загрузить запись (можно ужесточить)

    async def can_delete(self, room_id: int, user_id: int) -> bool:
        m = await self.mrepo.get_active(room_id=room_id, user_id=user_id)
        return bool(m and m.role in ("owner", "admin"))

    async def save_file(self, *, room_slug: str, uploader_user_id: int, filename: str, file_obj, title: str, duration_sec: int | None) -> dict:
        room = await self._room(room_slug)
        if not await self.can_upload(room.id, uploader_user_id):
            raise PermissionError("forbidden")
        target_dir = self.base_dir / room.slug
        target_dir.mkdir(parents=True, exist_ok=True)
        dest = target_dir / filename
        with dest.open("wb") as out:
            shutil.copyfileobj(file_obj, out)
        file_url = f"/static/records/{room.slug}/{dest.name}"
        rec = await self.rec_repo.create(room_id=room.id, uploader_user_id=uploader_user_id, title=title, file_url=file_url, duration_sec=duration_sec)
        return {"id": rec.id, "title": rec.title, "file_url": rec.file_url, "duration_sec": rec.duration_sec}

    async def list(self, *, room_slug: str, limit: int = 100) -> list[dict]:
        room = await self._room(room_slug)
        items = await self.rec_repo.list_for_room(room_id=room.id, limit=limit)
        return [{"id": r.id, "title": r.title, "file_url": r.file_url, "duration_sec": r.duration_sec, "created_at": r.created_at.isoformat()+"Z"} for r in items]

    async def delete(self, *, room_slug: str, rec_id: int, actor_user_id: int) -> bool:
        room = await self._room(room_slug)
        if not await self.can_delete(room.id, actor_user_id):
            raise PermissionError("forbidden")
        return await self.rec_repo.delete(rec_id=rec_id)
