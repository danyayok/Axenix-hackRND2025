import re
from typing import Optional, Tuple, Sequence
from app.repositories.message_repo import MessageRepository
from app.repositories.room_repo import RoomRepository
from app.repositories.user_repo import UserRepository
from app.models.message import Message

_MAX_LEN = 2000
# очень базовая фильтрация: уберём управляющие, нормализуем пробелы
_ctrl = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
_ws = re.compile(r"\s+")

# (опционально) простой стоп-лист для MVP; расширим потом
_BAD = {"fuck", "shit"}  # пример; можно убрать совсем, если не нужно

class ChatService:
    def __init__(self, m_repo: MessageRepository, r_repo: RoomRepository, u_repo: UserRepository):
        self.m_repo = m_repo
        self.r_repo = r_repo
        self.u_repo = u_repo

    def _sanitize(self, text: str) -> str:
        text = _ctrl.sub("", text).strip()
        text = _ws.sub(" ", text)
        return text[:_MAX_LEN]

    def _validate(self, text: str) -> Optional[str]:
        if not text:
            return "empty"
        low = text.lower()
        if any(bad in low for bad in _BAD):
            return "forbidden"
        return None

    async def send(self, *, room_slug: str, user_id: int, text: str) -> Message:
        room = await self.r_repo.get_by_slug(room_slug)
        if not room:
            raise ValueError("room_not_found")
        user = await self.u_repo.get(user_id)
        if not user:
            raise ValueError("user_not_found")

        cleaned = self._sanitize(text)
        err = self._validate(cleaned)
        if err:
            raise ValueError(f"invalid_{err}")

        return await self.m_repo.create(room_id=room.id, user_id=user_id, text=cleaned)

    async def history(
        self, *, room_slug: str, limit: int = 50, before_id: Optional[int] = None
    ) -> Tuple[Sequence[Message], bool]:
        room = await self.r_repo.get_by_slug(room_slug)
        if not room:
            raise ValueError("room_not_found")
        return await self.m_repo.list_room(room_id=room.id, limit=limit, before_id=before_id)
