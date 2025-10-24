from pydantic import BaseModel, Field

class GuestTokenIn(BaseModel):
    user_id: int = Field(ge=1)

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
