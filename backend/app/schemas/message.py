from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class MessageCreate(BaseModel):
    user_id: int
    text: str
    is_encrypted: Optional[bool] = False
    enc_algo: Optional[str] = None

class MessageOut(BaseModel):
    id: int
    room_id: int
    user_id: int
    text: str
    created_at: datetime
    is_encrypted: bool
    enc_algo: Optional[str] = None

    class Config:
        from_attributes = True

class HistoryOut(BaseModel):
    items: List[MessageOut]

# Существующие схемы для шифрования
class EncryptedMessageCreate(BaseModel):
    user_id: int
    encrypted_text: str
    enc_algo: str

class MessageDeleteRequest(BaseModel):
    actor_user_id: int