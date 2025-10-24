from typing import Sequence, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.message import Message

class MessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, *, room_id: int, user_id: int, text: str) -> Message:
        m = Message(room_id=room_id, user_id=user_id, text=text)
        self.session.add(m)
        await self.session.flush()
        await self.session.refresh(m)
        return m

    async def list_room(
        self, *, room_id: int, limit: int = 50, before_id: Optional[int] = None
    ) -> Tuple[Sequence[Message], bool]:
        q = select(Message).where(Message.room_id == room_id)
        if before_id is not None:
            q = q.where(Message.id < before_id)
        q = q.order_by(Message.id.desc()).limit(limit + 1)
        res = await self.session.execute(q)
        items = list(res.scalars().all())
        has_more = len(items) > limit
        if has_more:
            items = items[:limit]
        items.reverse()  # в хронологическом порядке старые→новые
        return items, has_more
