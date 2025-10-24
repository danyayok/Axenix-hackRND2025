from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    room_slug: str
    user_id: int
    text: str
    created_at: datetime

class ChatHistoryOut(BaseModel):
    items: List[ChatMessageOut]
    has_more: bool
    next_before_id: Optional[int] = None
