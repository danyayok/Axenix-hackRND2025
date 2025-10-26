from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.deps import get_db
from app.repositories.notification_repo import NotificationRepository
from app.schemas.notification import NotificationOut, NotificationCreate

router = APIRouter()

@router.get("/{user_id}", response_model=List[NotificationOut])
async def get_user_notifications(
    user_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    repo = NotificationRepository(db)
    notifications = await repo.get_user_notifications(user_id, limit)
    return notifications

@router.post("/{user_id}/read/{notification_id}")
async def mark_notification_as_read(
    user_id: int,
    notification_id: int,
    db: AsyncSession = Depends(get_db)
):
    repo = NotificationRepository(db)
    notification = await repo.mark_as_read(notification_id, user_id)
    if not notification:
        raise HTTPException(404, "Notification not found")
    return {"message": "Notification marked as read"}

@router.post("/{user_id}/read-all")
async def mark_all_notifications_as_read(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    repo = NotificationRepository(db)
    count = await repo.mark_all_as_read(user_id)
    return {"message": f"{count} notifications marked as read"}

@router.get("/{user_id}/unread-count")
async def get_unread_count(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    repo = NotificationRepository(db)
    count = await repo.get_unread_count(user_id)
    return {"unread_count": count}