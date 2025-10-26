from pydantic import BaseModel
from typing import List, Optional

class RoomStateOut(BaseModel):
    room_slug: str
    topic: Optional[str] = None
    is_locked: bool = False
    mute_all: bool = False
    online_count: int = 0
    raised_hands: List[int] = []

class SetTopicIn(BaseModel):
    topic: str

class ToggleIn(BaseModel):
    value: bool