from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Membership(Base):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("room.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20), default="guest")     # owner|admin|guest
    status: Mapped[str] = mapped_column(String(10), default="active")  # active|left
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    left_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # состояние участника
    hand_raised: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mic_muted:  Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cam_off:    Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # модерация
    admin_muted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
