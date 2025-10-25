from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class UserCreate(BaseModel):
    nickname: str = Field(min_length=1, max_length=80)
    avatar_url: Optional[str] = None
    public_key_pem: Optional[str] = None  # NEW

class UserUpdate(BaseModel):
    nickname: Optional[str] = Field(default=None, min_length=1, max_length=80)
    avatar_url: Optional[str] = None
    public_key_pem: Optional[str] = None  # NEW

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nickname: str
    avatar_url: Optional[str] = None
    public_key_pem: Optional[str] = None
