from pydantic import BaseModel, Field

class TargetUserIn(BaseModel):
    user_id: int = Field(ge=1)

class ForceMuteIn(TargetUserIn):
    muted: bool

class RoleOut(BaseModel):
    user_id: int
    role: str

class ForceMuteOut(BaseModel):
    user_id: int
    admin_muted: bool
    mic_muted: bool

class KickOut(BaseModel):
    user_id: int

# NEW
class SpeakIn(TargetUserIn):
    can_speak: bool

class SpeakOut(BaseModel):
    user_id: int
    can_speak: bool

class ForceVideoIn(TargetUserIn):
    video_off: bool

class ForceVideoOut(BaseModel):
    user_id: int
    admin_video_off: bool
    cam_off: bool
