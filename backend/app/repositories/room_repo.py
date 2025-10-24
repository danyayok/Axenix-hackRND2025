from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Room

class RoomRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        slug: str,
        title: str,
        is_private: bool,
        invite_key: Optional[str],
        created_by: Optional[str],
    ) -> Room:
        room = Room(
            slug=slug,
            title=title,
            is_private=is_private,
            invite_key=invite_key,
            created_by=created_by,
        )
        self.session.add(room)
        await self.session.flush()
        await self.session.refresh(room)
        return room

    async def get_by_id(self, room_id: int) -> Optional[Room]:
        q = await self.session.execute(select(Room).where(Room.id == room_id))
        return q.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Room]:
        q = await self.session.execute(select(Room).where(Room.slug == slug))
        return q.scalar_one_or_none()

    async def get_by_invite_key(self, invite_key: str) -> Optional[Room]:
        q = await self.session.execute(select(Room).where(Room.invite_key == invite_key))
        return q.scalar_one_or_none()

    async def list(self, limit: int = 50, offset: int = 0) -> Sequence[Room]:
        q = await self.session.execute(
            select(Room).order_by(Room.id.desc()).limit(limit).offset(offset)
        )
        return q.scalars().all()

    async def slug_exists(self, slug: str) -> bool:
        q = await self.session.execute(select(Room.id).where(Room.slug == slug))
        return q.scalar_one_or_none() is not None

    async def invite_exists(self, invite_key: str) -> bool:
        q = await self.session.execute(select(Room.id).where(Room.invite_key == invite_key))
        return q.scalar_one_or_none() is not None
