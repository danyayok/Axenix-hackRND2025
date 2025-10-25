from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Recording(Base):
    __tablename__ = "recording"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("room.id", ondelete="CASCADE"), index=True)
    uploader_user_id: Mapped[int] = mapped_column(index=True)
    title: Mapped[str] = mapped_column(String(200))
    file_url: Mapped[str] = mapped_column(String(255))  # /static/records/<slug>/...
    duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
