from typing import Optional

from app.repositories.room_repo import RoomRepository
from app.utils.ids import gen_slug, normalize_title_to_slug_hint, gen_invite_key
from app.core.config import settings
from app.models.room import Room

class RoomService:
    def __init__(self, repo: RoomRepository):
        self.repo = repo

    async def create_room(
        self,
        *,
        title: str,
        is_private: bool,
        create_invite: bool,
        created_by: Optional[str],
    ) -> Room:
        base = normalize_title_to_slug_hint(title)
        slug = base or gen_slug(8)
        i = 0
        while await self.repo.slug_exists(slug):
            i += 1
            slug = f"{base}-{gen_slug(4)}" if i < 7 else gen_slug(10)

        invite_key = gen_invite_key(16) if create_invite else None
        if invite_key and await self.repo.invite_exists(invite_key):
            invite_key = gen_invite_key(18)

        room = await self.repo.create(
            slug=slug,
            title=title,
            is_private=is_private,
            invite_key=invite_key,
            created_by=created_by,
        )
        return room

    def make_invite_url(self, room: Room) -> Optional[str]:
        if not room.invite_key:
            return None
        base = settings.public_base_url.rstrip("/")
        return f"{base}/join/{room.invite_key}"
