from datetime import datetime, timedelta
from app.repositories.membership_repo import MembershipRepository
from app.repositories.room_repo import RoomRepository
from app.repositories.user_repo import UserRepository
from app.models.membership import Membership

ONLINE_TTL_SECONDS = 45  # если heartbeat старше — считаем оффлайн для списка

class ParticipantService:
    def __init__(self, m_repo: MembershipRepository, r_repo: RoomRepository, u_repo: UserRepository):
        self.m_repo = m_repo
        self.r_repo = r_repo
        self.u_repo = u_repo

    async def join(self, *, room_slug: str, user_id: int, invite_key: str | None) -> Membership:
        room = await self.r_repo.get_by_slug(room_slug)
        if not room:
            raise ValueError("room_not_found")

        if room.is_private:
            if not invite_key or invite_key != room.invite_key:
                raise ValueError("invite_required_or_invalid")

        user = await self.u_repo.get(user_id)
        if not user:
            raise ValueError("user_not_found")

        existing = await self.m_repo.get_active(room_id=room.id, user_id=user_id)
        if existing:
            # просто обновим last_seen
            existing.last_seen = datetime.utcnow()
            return existing

        return await self.m_repo.create_active(room_id=room.id, user_id=user_id)

    async def leave(self, *, room_slug: str, user_id: int) -> Membership | None:
        room = await self.r_repo.get_by_slug(room_slug)
        if not room:
            return None
        return await self.m_repo.mark_left(room_id=room.id, user_id=user_id)

    async def heartbeat(self, *, room_slug: str, user_id: int) -> Membership | None:
        room = await self.r_repo.get_by_slug(room_slug)
        if not room:
            return None
        return await self.m_repo.heartbeat(room_id=room.id, user_id=user_id)

    async def list(self, *, room_slug: str) -> list[dict]:
        room = await self.r_repo.get_by_slug(room_slug)
        if not room:
            raise ValueError("room_not_found")
        ms = await self.m_repo.list_by_room(room_id=room.id)
        now = datetime.utcnow()
        res: list[dict] = []
        for m in ms:
            is_online = (m.status == "active") and (now - m.last_seen <= timedelta(seconds=ONLINE_TTL_SECONDS))
            res.append({
                "membership_id": m.id,
                "room_slug": room.slug,
                "user_id": m.user_id,
                "role": m.role,
                "status": m.status if is_online else "left" if m.status == "left" else "offline",
                "last_seen": m.last_seen,
                "is_online": is_online,
            })
        return res
