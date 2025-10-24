from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

class RoomStateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    room_slug: str
    topic: Optional[str] = None
    is_locked: bool
    mute_all: bool
    online_count: int
    raised_hands: List[int]  # user_id список

class SetTopicIn(BaseModel):
    topic: Optional[str] = Field(default=None, max_length=200)

class ToggleIn(BaseModel):
    value: bool
