from typing import Sequence, Optional
from time import time
from collections import defaultdict

from app.repositories.message_repo import MessageRepository
from app.repositories.room_repo import RoomRepository
from app.repositories.user_repo import UserRepository
from app.models.message import Message
from app.utils.text import sanitize_message, has_bad_words

# in-memory rate limit: 5 сообщений / 10с на (room, user)
_BUCKET: dict[tuple[int,int], list[float]] = defaultdict(list)
_LIMIT = 5
_WINDOW = 10.0

class ChatService:
    def __init__(self, m_repo: MessageRepository, r_repo: RoomRepository, u_repo: UserRepository):
        self.m_repo = m_repo
        self.r_repo = r_repo
        self.u_repo = u_repo

    async def send(self, *, room_slug: str, user_id: int, text: str) -> Message:
        room = await self.r_repo.get_by_slug(room_slug)
        if not room:
            raise ValueError("room_not_found")

        user = await self.u_repo.get(user_id)
        if not user:
            raise ValueError("user_not_found")

        msg = sanitize_message(text)
        if not msg:
            raise ValueError("empty_message")
        if has_bad_words(msg):
            raise ValueError("forbidden_words")

        # rate-limit
        key = (room.id, user_id)
        now = time()
        bucket = _BUCKET[key]
        # drop old
        while bucket and now - bucket[0] > _WINDOW:
            bucket.pop(0)
        if len(bucket) >= _LIMIT:
            raise ValueError("rate_limited")
        bucket.append(now)

        return await self.m_repo.create(room_id=room.id, user_id=user_id, text=msg)

    async def history(self, *, room_slug: str, limit: int = 50, before_id: Optional[int] = None) -> Sequence[Message]:
        room = await self.r_repo.get_by_slug(room_slug)
        if not room:
            raise ValueError("room_not_found")
        return await self.m_repo.list_history(room_id=room.id, limit=limit, before_id=before_id)

    async def delete(self, *, room_slug: str, message_id: int) -> bool:
        room = await self.r_repo.get_by_slug(room_slug)
        if not room:
            raise ValueError("room_not_found")
        return await self.m_repo.delete(message_id=message_id)
