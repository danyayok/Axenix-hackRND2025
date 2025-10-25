from typing import Optional, Sequence
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.crypto import RoomKey, RoomKeyShare

class CryptoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_room_key(self, *, room_id: int, created_by: int, algo: str = "AES-256-GCM") -> RoomKey:
        rk = RoomKey(room_id=room_id, created_by=created_by, algo=algo, status="active")
        self.session.add(rk)
        await self.session.flush()
        await self.session.refresh(rk)
        return rk

    async def add_share(self, *, room_key_id: int, room_id: int, user_id: int, wrapped_key_b64: str) -> RoomKeyShare:
        sh = RoomKeyShare(room_key_id=room_key_id, room_id=room_id, user_id=user_id, wrapped_key_b64=wrapped_key_b64)
        self.session.add(sh)
        await self.session.flush()
        await self.session.refresh(sh)
        return sh

    async def latest_share_for_user(self, *, room_id: int, user_id: int) -> Optional[RoomKeyShare]:
        res = await self.session.execute(
            select(RoomKeyShare)
            .where(RoomKeyShare.room_id == room_id, RoomKeyShare.user_id == user_id)
            .order_by(desc(RoomKeyShare.id))
            .limit(1)
        )
        return res.scalar_one_or_none()

    async def list_shares_for_room(self, *, room_id: int) -> Sequence[RoomKeyShare]:
        res = await self.session.execute(select(RoomKeyShare).where(RoomKeyShare.room_id == room_id))
        return res.scalars().all()
