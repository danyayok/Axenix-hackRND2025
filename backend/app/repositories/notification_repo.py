from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification

class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, room_slug: str, title: str, message: str, type: str = "conference_created") -> Notification:
        notification = Notification(
            user_id=user_id,
            room_slug=room_slug,
            title=title,
            message=message,
            type=type
        )
        self.session.add(notification)
        await self.session.flush()
        await self.session.refresh(notification)
        return notification

    async def get_user_notifications(self, user_id: int, limit: int = 50) -> List[Notification]:
        q = await self.session.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        return q.scalars().all()

    async def mark_as_read(self, notification_id: int, user_id: int) -> Optional[Notification]:
        q = await self.session.execute(
            select(Notification)
            .where(Notification.id == notification_id)
            .where(Notification.user_id == user_id)
        )
        notification = q.scalar_one_or_none()
        if notification:
            notification.is_read = True
            await self.session.flush()
        return notification

    async def mark_all_as_read(self, user_id: int) -> int:
        q = await self.session.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.is_read == False)
        )
        notifications = q.scalars().all()
        for notification in notifications:
            notification.is_read = True
        await self.session.flush()
        return len(notifications)

    async def get_unread_count(self, user_id: int) -> int:
        q = await self.session.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.is_read == False)
        )
        return len(q.scalars().all())