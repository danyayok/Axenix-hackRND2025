from typing import List
from app.repositories.room_repo import RoomRepository
from app.repositories.membership_repo import MembershipRepository
from app.services.participants import ONLINE_TTL_SECONDS
from datetime import datetime, timedelta
from app.models.room import Room

class StateService:
    def __init__(self, r_repo: RoomRepository, m_repo: MembershipRepository):
        self.r_repo = r_repo
        self.m_repo = m_repo

    async def _room_or_err(self, slug: str) -> Room:
        room = await self.r_repo.get_by_slug(slug)
        if not room:
            raise ValueError("room_not_found")
        return room

    async def snapshot(self, room_slug: str) -> dict:
        room = await self._room_or_err(room_slug)
        members = await self.m_repo.list_by_room(room_id=room.id)
        now = datetime.utcnow()
        online = sum(1 for m in members if m.status == "active" and (now - m.last_seen) <= timedelta(seconds=ONLINE_TTL_SECONDS))
        raised = [m.user_id for m in members if m.hand_raised]
        return {
            "room_slug": room.slug,
            "topic": room.topic,
            "is_locked": room.is_locked,
            "mute_all": room.mute_all,
            "online_count": online,
            "raised_hands": raised,
        }

    async def set_topic(self, room_slug: str, topic: str | None) -> dict:
        room = await self._room_or_err(room_slug)
        await self.r_repo.set_topic(room, topic)
        return await self.snapshot(room_slug)

    async def set_locked(self, room_slug: str, locked: bool) -> dict:
        room = await self._room_or_err(room_slug)
        await self.r_repo.set_locked(room, locked)
        return await self.snapshot(room_slug)

    async def set_mute_all(self, room_slug: str, mute: bool) -> dict:
        room = await self._room_or_err(room_slug)
        await self.r_repo.set_mute_all(room, mute)
        return await self.snapshot(room_slug)

    async def set_hand(self, room_slug: str, user_id: int, raised: bool) -> dict:
        room = await self._room_or_err(room_slug)
        m = await self.m_repo.set_hand(room_id=room.id, user_id=user_id, raised=raised)
        if not m:
            raise ValueError("membership_not_found")
        return await self.snapshot(room_slug)
