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
