from pydantic import BaseModel, Field
from pydantic import BaseModel, EmailStr

class GuestTokenIn(BaseModel):
    user_id: int

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class GuestTokenIn(BaseModel):
    user_id: int = Field(ge=1)