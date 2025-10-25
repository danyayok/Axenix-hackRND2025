from typing import Sequence, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.message import Message

class MessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, *, room_id: int, user_id: int, text: str, is_encrypted: bool = False, enc_algo: str | None = None
    ) -> Message:
        m = Message(room_id=room_id, user_id=user_id, text=text, is_encrypted=is_encrypted, enc_algo=enc_algo)
        self.session.add(m)
        await self.session.flush()
        await self.session.refresh(m)
        return m

    async def list_history(self, *, room_id: int, limit: int = 50, before_id: Optional[int] = None) -> Sequence[Message]:
        stmt = select(Message).where(Message.room_id == room_id)
        if before_id:
            stmt = stmt.where(Message.id < before_id)
        stmt = stmt.order_by(desc(Message.id)).limit(max(1, min(limit, 200)))
        res = await self.session.execute(stmt)
        items = list(res.scalars().all())
        items.reverse()
        return items

    async def get(self, *, message_id: int) -> Optional[Message]:
        res = await self.session.execute(select(Message).where(Message.id == message_id))
        return res.scalar_one_or_none()

    async def delete(self, *, message_id: int) -> bool:
        m = await self.get(message_id=message_id)
        if not m:
            return False
        await self.session.delete(m)
        await self.session.flush()
        return True
