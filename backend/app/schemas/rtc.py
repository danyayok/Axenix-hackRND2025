from pydantic import BaseModel

class TokenRequest(BaseModel):
    username: str
    room_name: str

class TokenResponse(BaseModel):
    token: str
    server_url: str
    room_name: str

class RTCIceServer(BaseModel):
    urls: str
    username: str | None = None
    credential: str | None = None

class RTCConfigOut(BaseModel):
    iceServers: list[RTCIceServer]