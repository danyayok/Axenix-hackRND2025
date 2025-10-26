from datetime import datetime, timedelta
from app.repositories.membership_repo import MembershipRepository
from app.repositories.room_repo import RoomRepository
from app.repositories.user_repo import UserRepository
from app.models.membership import Membership

ONLINE_TTL_SECONDS = 45

class ParticipantService:
    def __init__(self, m_repo: MembershipRepository, r_repo: RoomRepository, u_repo: UserRepository):
        self.m_repo = m_repo
        self.r_repo = r_repo  # room_repo
        self.u_repo = u_repo  # user_repo

    async def join(self, room_slug: str, user_id: int, invite_key: str | None = None) -> Membership:
        # ИСПРАВЛЕННЫЕ НАЗВАНИЯ АТРИБУТОВ:
        room = await self.r_repo.get_by_slug(room_slug)  # было: self.room_repo
        if not room:
            raise ValueError("room_not_found")

        user = await self.u_repo.get(user_id)  # было: self.user_repo
        if not user:
            raise ValueError("user_not_found")

        # ПРОВЕРЯЕМ, ЯВЛЯЕТСЯ ЛИ ПОЛЬЗОВАТЕЛЬ СОЗДАТЕЛЕМ КОМНАТЫ
        is_creator = room.created_by == user_id

        # Если пользователь создатель комнаты - пропускаем все проверки
        if is_creator:
            print(f"DEBUG: creator joining room, bypassing checks")
        else:
            # Для НЕ-создателей проверяем блокировку комнаты
            if room.is_locked:
                print(f"DEBUG: room is locked, user is not creator")
                raise ValueError("room_locked")

            # Для НЕ-создателей проверяем приватность комнаты
            if room.is_private:
                if not invite_key or invite_key != room.invite_key:
                    print(f"DEBUG: invalid invite - expected: {room.invite_key}, got: {invite_key}")
                    raise ValueError("invite_required_or_invalid")

        # Проверяем, не присоединен ли уже пользователь
        existing = await self.m_repo.get_active(room_id=room.id, user_id=user_id)  # было: self.membership_repo
        if existing:
            # Обновляем last_seen если уже присоединен
            existing.last_seen = datetime.utcnow()
            # Используем session из репозитория для flush
            await self.m_repo.session.flush()  # было: self.db
            await self.m_repo.session.refresh(existing)
            return existing

        # Создаем новое членство
        membership = Membership(
            room_id=room.id,
            user_id=user_id,
            role="owner" if is_creator else "participant",  # Создатель становится owner
            status="active",
            last_seen=datetime.utcnow(),
        )

        self.m_repo.session.add(membership)  # было: self.db
        await self.m_repo.session.flush()    # было: self.db
        await self.m_repo.session.refresh(membership)  # было: self.db

        print(f"DEBUG: user {user_id} joined room {room_slug} as {membership.role}")
        return membership

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
                "mic_muted": m.mic_muted,
                "cam_off": m.cam_off,
                "hand_raised": m.hand_raised,
            })
        return res