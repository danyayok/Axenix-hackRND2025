from pydantic import BaseModel
from datetime import datetime

class NotificationCreate(BaseModel):
    user_id: int
    room_slug: str
    title: str
    message: str
    type: str = "conference_created"

class NotificationOut(BaseModel):
    id: int
    user_id: int
    room_slug: str
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True