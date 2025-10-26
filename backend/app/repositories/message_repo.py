from typing import List, Optional
from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.message import Message


class MessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # СУЩЕСТВУЮЩИЕ ФУНКЦИИ (не меняем)
    async def create(self, room_id: int, user_id: int, text: str, is_encrypted: bool = False,
                     enc_algo: Optional[str] = None) -> Message:
        """Создать сообщение (существующая функция)"""
        message = Message(
            room_id=room_id,
            user_id=user_id,
            text=text,
            is_encrypted=is_encrypted,
            enc_algo=enc_algo
        )
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def get(self, message_id: int) -> Optional[Message]:
        """Получить сообщение по ID (существующая функция)"""
        result = await self.session.execute(select(Message).where(Message.id == message_id))
        return result.scalar_one_or_none()

    async def get_room_messages(self, room_id: int, limit: int = 50, before_id: Optional[int] = None) -> List[Message]:
        """Получить историю сообщений комнаты (существующая функция)"""
        query = select(Message).where(Message.room_id == room_id)

        if before_id:
            query = query.where(Message.id < before_id)

        query = query.order_by(desc(Message.created_at)).limit(limit)

        result = await self.session.execute(query)
        messages = result.scalars().all()
        return list(reversed(messages))  # Возвращаем в правильном порядке

    async def delete(self, message_id: int) -> bool:
        """Удалить сообщение (существующая функция)"""
        message = await self.get(message_id)
        if message:
            await self.session.delete(message)
            await self.session.flush()
            return True
        return False

    async def get_user_messages(self, user_id: int, limit: int = 50) -> List[Message]:
        """Получить сообщения пользователя (существующая функция)"""
        result = await self.session.execute(
            select(Message)
            .where(Message.user_id == user_id)
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def search_in_room(self, room_id: int, search_text: str, limit: int = 20) -> List[Message]:
        """Поиск сообщений в комнате (существующая функция)"""
        result = await self.session.execute(
            select(Message)
            .where(and_(
                Message.room_id == room_id,
                Message.text.ilike(f"%{search_text}%")
            ))
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    # НОВЫЕ ФУНКЦИИ (добавляем для удобства)
    async def get_recent_room_messages(self, room_id: int, limit: int = 20) -> List[Message]:
        """Получить последние сообщения комнаты (новая функция)"""
        result = await self.session.execute(
            select(Message)
            .where(Message.room_id == room_id)
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def count_room_messages(self, room_id: int) -> int:
        """Посчитать количество сообщений в комнате (новая функция)"""
        result = await self.session.execute(
            select(Message).where(Message.room_id == room_id)
        )
        return len(result.scalars().all())

    # Алиасы для совместимости (если где-то использовались старые названия)
    get_message = get
    delete_message = delete
    get_messages_by_room = get_room_messages