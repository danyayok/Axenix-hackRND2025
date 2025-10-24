from typing import Optional, Sequence
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.membership import Membership

class MembershipRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_active(self, *, room_id: int, user_id: int, role: str = "guest") -> Membership:
        m = Membership(room_id=room_id, user_id=user_id, role=role, status="active")
        self.session.add(m)
        await self.session.flush()
        await self.session.refresh(m)
        return m

    async def get_active(self, *, room_id: int, user_id: int) -> Optional[Membership]:
        q = await self.session.execute(
            select(Membership).where(
                Membership.room_id == room_id,
                Membership.user_id == user_id,
                Membership.status == "active",
            )
        )
        return q.scalar_one_or_none()

    async def mark_left(self, *, room_id: int, user_id: int) -> Optional[Membership]:
        m = await self.get_active(room_id=room_id, user_id=user_id)
        if not m:
            return None
        m.status = "left"
        from datetime import datetime
        m.left_at = datetime.utcnow()
        await self.session.flush()
        await self.session.refresh(m)
        return m

    async def heartbeat(self, *, room_id: int, user_id: int) -> Optional[Membership]:
        m = await self.get_active(room_id=room_id, user_id=user_id)
        if not m:
            return None
        from datetime import datetime
        m.last_seen = datetime.utcnow()
        await self.session.flush()
        await self.session.refresh(m)
        return m

    async def list_by_room(self, *, room_id: int, limit: int = 200) -> Sequence[Membership]:
        q = await self.session.execute(
            select(Membership).where(Membership.room_id == room_id).order_by(Membership.id.desc()).limit(limit)
        )
        return q.scalars().all()
