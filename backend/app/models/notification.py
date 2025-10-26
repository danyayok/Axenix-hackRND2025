from datetime import datetime
from sqlalchemy import String, DateTime, Text, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Notification(Base):
    __tablename__ = "notification"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    room_slug: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(50), default="conference_created")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)