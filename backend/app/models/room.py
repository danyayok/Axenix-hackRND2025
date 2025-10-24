from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class Room(Base):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    is_private: Mapped[bool] = mapped_column(Boolean, default=False)
    invite_key: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("slug", name="uq_room_slug"),
        UniqueConstraint("invite_key", name="uq_room_invite_key"),
    )
