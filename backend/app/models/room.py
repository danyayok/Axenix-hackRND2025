from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Room(Base):
    __tablename__ = "room"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    title: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # приватный доступ по ключу-приглашению (если нужен)
    invite_key: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # состояние комнаты
    topic: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mute_all: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # NEW: индикатор активной записи (для UI и политики на фронте)
    recording_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # автор/метаданные
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
