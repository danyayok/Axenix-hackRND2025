from app.repositories.room_repo import RoomRepository
from app.repositories.membership_repo import MembershipRepository

class ModerationService:
    def __init__(self, r_repo: RoomRepository, m_repo: MembershipRepository):
        self.r_repo = r_repo
        self.m_repo = m_repo

    async def _room_or_err(self, slug: str):
        room = await self.r_repo.get_by_slug(slug)
        if not room: raise ValueError("room_not_found")
        return room

    async def promote(self, room_slug: str, target_user_id: int):
        room = await self._room_or_err(room_slug)
        m = await self.m_repo.set_role(room_id=room.id, user_id=target_user_id, role="admin")
        if not m: raise ValueError("membership_not_found")
        return {"user_id": m.user_id, "role": m.role}

    async def demote(self, room_slug: str, target_user_id: int):
        room = await self._room_or_err(room_slug)
        m = await self.m_repo.set_role(room_id=room.id, user_id=target_user_id, role="guest")
        if not m: raise ValueError("membership_not_found")
        return {"user_id": m.user_id, "role": m.role}

    async def force_mute(self, room_slug: str, target_user_id: int, muted: bool):
        room = await self._room_or_err(room_slug)
        m = await self.m_repo.set_admin_muted(room_id=room.id, user_id=target_user_id, muted=muted)
        if not m: raise ValueError("membership_not_found")
        return {"user_id": m.user_id, "admin_muted": m.admin_muted, "mic_muted": m.mic_muted}

    async def kick(self, room_slug: str, target_user_id: int):
        room = await self._room_or_err(room_slug)
        m = await self.m_repo.kick(room_id=room.id, user_id=target_user_id)
        if not m: raise ValueError("membership_not_found")
        return {"user_id": m.user_id}

    # NEW: выдача/снятие права выступления
    async def set_speaker(self, room_slug: str, target_user_id: int, can_speak: bool):
        room = await self._room_or_err(room_slug)
        m = await self.m_repo.set_can_speak(room_id=room.id, user_id=target_user_id, can_speak=can_speak)
        if not m: raise ValueError("membership_not_found")
        return {"user_id": m.user_id, "can_speak": m.can_speak}

    # NEW: принудительно выключить/разрешить видео
    async def set_video_off(self, room_slug: str, target_user_id: int, video_off: bool):
        room = await self._room_or_err(room_slug)
        m = await self.m_repo.set_admin_video_off(room_id=room.id, user_id=target_user_id, video_off=video_off)
        if not m: raise ValueError("membership_not_found")
        return {"user_id": m.user_id, "admin_video_off": m.admin_video_off, "cam_off": m.cam_off}
