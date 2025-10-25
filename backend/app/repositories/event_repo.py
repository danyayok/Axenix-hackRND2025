from typing import Optional, Sequence
from sqlalchemy import select, and_, asc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event import EventLog

class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def append(self, *, room_id: int, type_: str, payload_json: str) -> EventLog:
        e = EventLog(room_id=room_id, type=type_, payload=payload_json)
        self.session.add(e)
        await self.session.flush()
        await self.session.refresh(e)
        return e

    async def list_after(self, *, room_id: int, after_seq: int, limit: int = 200) -> Sequence[EventLog]:
        q = select(EventLog).where(
            and_(EventLog.room_id == room_id, EventLog.id > after_seq)
        ).order_by(asc(EventLog.id)).limit(max(1, min(limit, 500)))
        res = await self.session.execute(q)
        return res.scalars().all()

    async def next_seq(self) -> int:
        # Возвращаем "следующий" seq: максимум id + 1 (для информирования клиента).
        q = await self.session.execute(select(EventLog).order_by(EventLog.id.desc()).limit(1))
        last = q.scalar_one_or_none()
        return (last.id + 1) if last else 1
