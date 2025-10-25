from typing import Dict, Any
from app.repositories.room_repo import RoomRepository
from app.repositories.membership_repo import MembershipRepository

class StateService:
    def __init__(self, rrepo: RoomRepository, mrepo: MembershipRepository):
        self.rrepo = rrepo
        self.mrepo = mrepo

    async def snapshot(self, room_slug: str) -> Dict[str, Any]:
        room = await self.rrepo.get_by_slug(room_slug)
        if not room:
            raise ValueError("room_not_found")

        # соберём счётчики рук (если используешь их в UI)
        members = await self.mrepo.list_by_room(room_id=room.id, limit=500)
        hands_up = [m.user_id for m in members if m.hand_raised]

        return {
            "room_slug": room.slug,
            "topic": room.topic,
            "is_locked": bool(room.is_locked),
            "mute_all": bool(room.mute_all),
            # NEW:
            "recording_active": bool(room.recording_active),
            "hands_up": hands_up,
        }

    async def set_topic(self, room_slug: str, topic: str | None) -> Dict[str, Any]:
        room = await self.rrepo.get_by_slug(room_slug)
        if not room:
            raise ValueError("room_not_found")
        room.topic = (topic or "").strip() or None
        return {
            "room_slug": room.slug,
            "topic": room.topic,
            "is_locked": bool(room.is_locked),
            "mute_all": bool(room.mute_all),
            "recording_active": bool(room.recording_active),
        }

    async def set_locked(self, room_slug: str, locked: bool) -> Dict[str, Any]:
        room = await self.rrepo.get_by_slug(room_slug)
        if not room:
            raise ValueError("room_not_found")
        room.is_locked = bool(locked)
        return {
            "room_slug": room.slug,
            "topic": room.topic,
            "is_locked": bool(room.is_locked),
            "mute_all": bool(room.mute_all),
            "recording_active": bool(room.recording_active),
        }

    async def set_mute_all(self, room_slug: str, mute_all: bool) -> Dict[str, Any]:
        room = await self.rrepo.get_by_slug(room_slug)
        if not room:
            raise ValueError("room_not_found")
        room.mute_all = bool(mute_all)
        return {
            "room_slug": room.slug,
            "topic": room.topic,
            "is_locked": bool(room.is_locked),
            "mute_all": bool(room.mute_all),
            "recording_active": bool(room.recording_active),
        }

    async def set_hand(self, room_slug: str, user_id: int, raised: bool) -> Dict[str, Any]:
        room = await self.rrepo.get_by_slug(room_slug)
        if not room:
            raise ValueError("room_not_found")
        m = await self.mrepo.set_hand(room_id=room.id, user_id=user_id, raised=bool(raised))
        if not m:
            raise ValueError("membership_not_found")
        return {"user_id": m.user_id, "hand_raised": bool(m.hand_raised)}

    # NEW: включить/выключить индикатор записи
    async def set_recording(self, room_slug: str, active: bool) -> Dict[str, Any]:
        room = await self.rrepo.get_by_slug(room_slug)
        if not room:
            raise ValueError("room_not_found")
        room.recording_active = bool(active)
        return {
            "room_slug": room.slug,
            "topic": room.topic,
            "is_locked": bool(room.is_locked),
            "mute_all": bool(room.mute_all),
            "recording_active": bool(room.recording_active),
        }
