from pydantic import BaseModel
from typing import Optional, Any, Dict

class WsJoinAck(BaseModel):
    type: str = "joined"
    room_slug: str
    user_id: int

class WsMemberJoined(BaseModel):
    type: str = "member.joined"
    user_id: int

class WsMemberLeft(BaseModel):
    type: str = "member.left"
    user_id: int

class WsOffer(BaseModel):
    type: str = "offer"
    to: int
    sdp: str

class WsAnswer(BaseModel):
    type: str = "answer"
    to: int
    sdp: str

class WsIce(BaseModel):
    type: str = "ice"
    to: int
    candidate: Dict[str, Any]  # {candidate, sdpMid, sdpMLineIndex}
