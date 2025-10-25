from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class RoomKey(Base):
    __tablename__ = "roomkey"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("room.id", ondelete="CASCADE"), index=True)
    created_by: Mapped[int] = mapped_column(index=True)
    algo: Mapped[str] = mapped_column(String(50), default="AES-256-GCM")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active|rotated|revoked

class RoomKeyShare(Base):
    __tablename__ = "roomkeyshare"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    room_key_id: Mapped[int] = mapped_column(ForeignKey("roomkey.id", ondelete="CASCADE"), index=True)
    room_id: Mapped[int] = mapped_column(index=True)
    user_id: Mapped[int] = mapped_column(index=True)
    wrapped_key_b64: Mapped[str] = mapped_column(Text)  # RSA-OAEP base64
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
