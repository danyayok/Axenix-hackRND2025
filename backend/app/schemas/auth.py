from typing import Optional

from pydantic import BaseModel, Field
from pydantic import BaseModel, EmailStr

from app.schemas.user import UserOut


class GuestTokenIn(BaseModel):
    user_id: int

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: Optional[int] = None  # Добавляем поле
    user: Optional[UserOut] = None  # Добавляем данные пользователя

class GuestTokenIn(BaseModel):
    user_id: int = Field(ge=1)