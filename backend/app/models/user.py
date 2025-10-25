from datetime import datetime
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nickname: Mapped[str] = mapped_column(String(80), unique=False, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    public_key_pem: Mapped[str | None] = mapped_column(Text, nullable=True)  # NEW: PEM публичный ключ

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
