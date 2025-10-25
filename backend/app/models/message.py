from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Boolean, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Message(Base):
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("room.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # NEW: для зашифрованных сообщений
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    enc_algo: Mapped[str | None] = mapped_column(String(50), nullable=True)
