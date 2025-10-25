from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class EventLog(Base):
    """
    Последовательность событий комнаты.
    id – это глобальный seq внутри БД, но мы храним room_id для выборок по комнате.
    """
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # seq
    room_id: Mapped[int] = mapped_column(ForeignKey("room.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(50))     # e.g. chat.message, state.changed
    payload: Mapped[str] = mapped_column(String)      # JSON (текст)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
