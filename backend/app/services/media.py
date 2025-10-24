from typing import Optional
from app.repositories.room_repo import RoomRepository
from app.repositories.membership_repo import MembershipRepository

class MediaService:
    def __init__(self, r_repo: RoomRepository, m_repo: MembershipRepository):
        self.r_repo = r_repo
        self.m_repo = m_repo

    async def update_self(
        self,
        *, room_slug: str, user_id: int, mic_muted: Optional[bool] = None, cam_off: Optional[bool] = None
    ) -> dict:
        room = await self.r_repo.get_by_slug(room_slug)
        if not room:
            raise ValueError("room_not_found")
        m = await self.m_repo.set_media_flags(room_id=room.id, user_id=user_id, mic_muted=mic_muted, cam_off=cam_off)
        if not m:
            raise ValueError("membership_not_found")
        return {"user_id": m.user_id, "mic_muted": m.mic_muted, "cam_off": m.cam_off}
