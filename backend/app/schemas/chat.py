from pydantic import BaseModel, ConfigDict
from typing import List

class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    room_id: int
    user_id: int
    text: str
    created_at: str | None = None

class HistoryOut(BaseModel):
    items: List[MessageOut]
