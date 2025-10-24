from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class ParticipantJoinIn(BaseModel):
    room_slug: str
    user_id: int
    invite_key: Optional[str] = None  # для приватных комнат

class ParticipantLeaveIn(BaseModel):
    room_slug: str
    user_id: int

class ParticipantHeartbeatIn(BaseModel):
    room_slug: str
    user_id: int

class ParticipantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    membership_id: int
    room_slug: str
    user_id: int
    role: str
    status: str
    last_seen: datetime
    is_online: bool

class ParticipantListOut(BaseModel):
    participants: list[ParticipantOut]
