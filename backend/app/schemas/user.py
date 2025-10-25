from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    nickname: str
    avatar_url: Optional[str] = None
    public_key_pem: Optional[str] = None
    # ДОБАВЛЯЕМ ОПЦИОНАЛЬНЫЕ ПОЛЯ
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    public_key_pem: Optional[str] = None
    # И ДЛЯ ОБНОВЛЕНИЯ ТОЖЕ
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class UserOut(BaseModel):
    id: int
    nickname: str
    avatar_url: Optional[str] = None
    public_key_pem: Optional[str] = None
    email: Optional[str] = None