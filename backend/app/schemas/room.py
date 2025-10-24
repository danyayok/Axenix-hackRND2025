from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class RoomCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    is_private: bool = False
    create_invite: bool = True
    created_by: Optional[str] = None

class RoomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
    title: str
    is_private: bool
    invite_key: str | None = None
    invite_url: str | None = None

class RoomListItem(RoomOut):
    pass

class RoomJoinByInviteIn(BaseModel):
    invite_key: str

class RoomExistsOut(BaseModel):
    exists: bool
