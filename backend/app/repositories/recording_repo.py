from typing import Sequence, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.recording import Recording

class RecordingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, *, room_id: int, uploader_user_id: int, title: str, file_url: str, duration_sec: int | None = None) -> Recording:
        rec = Recording(room_id=room_id, uploader_user_id=uploader_user_id, title=title, file_url=file_url, duration_sec=duration_sec)
        self.session.add(rec); await self.session.flush(); await self.session.refresh(rec)
        return rec

    async def list_for_room(self, *, room_id: int, limit: int = 100) -> Sequence[Recording]:
        res = await self.session.execute(
            select(Recording).where(Recording.room_id == room_id).order_by(desc(Recording.id)).limit(limit)
        )
        return res.scalars().all()

    async def get(self, *, rec_id: int) -> Optional[Recording]:
        res = await self.session.execute(select(Recording).where(Recording.id == rec_id))
        return res.scalar_one_or_none()

    async def delete(self, *, rec_id: int) -> bool:
        rec = await self.get(rec_id=rec_id)
        if not rec: return False
        await self.session.delete(rec); await self.session.flush()
        return True
