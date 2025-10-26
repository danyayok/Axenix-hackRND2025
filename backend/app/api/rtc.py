from fastapi import APIRouter, HTTPException
import jwt
import time
from pydantic import BaseModel

from app.schemas.rtc import TokenRequest, TokenResponse, RTCConfigOut, RTCIceServer

router = APIRouter()

# КОНФИГУРАЦИЯ LIVEKIT - ОБНОВЛЕННЫЕ КЛЮЧИ
LIVEKIT_URL = "wss://livekit.myshore.ru"
LIVEKIT_API_KEY = "APISVzXeGWB2JZL"
LIVEKIT_API_SECRET = "8zsqNCiqHK7jAeDIj8VxYrIXRyyNzV7dRBFnRXoSMbC"


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


# В app/api/rtc.py исправьте функцию generate_livekit_token
@router.post("/token", response_model=TokenResponse)
async def generate_livekit_token(payload: TokenRequest):
    try:
        # Создаем payload для JWT токена согласно документации LiveKit
        now = int(time.time())
        expires = now + 3600  # 1 hour

        # ВАЖНО: identity обязательно для LiveKit
        if not payload.username or payload.username.strip() == "":
            raise HTTPException(400, "Username cannot be empty")

        video_grants = {
            "roomJoin": True,
            "room": payload.room_name,
            "canPublish": True,
            "canSubscribe": True,
            "canPublishData": True,
        }

        payload_jwt = {
            "exp": expires,
            "iat": now,
            "nbf": now,
            "iss": LIVEKIT_API_KEY,
            "sub": payload.username,  # sub должно совпадать с identity
            "video": video_grants,
            "name": payload.username,  # Отображаемое имя участника
        }

        # Генерируем JWT токен
        token = jwt.encode(
            payload_jwt,
            LIVEKIT_API_SECRET,
            algorithm="HS256"
        )

        return TokenResponse(
            token=token,
            server_url=LIVEKIT_URL,
            room_name=payload.room_name
        )

    except Exception as e:
        raise HTTPException(500, f"Error generating token: {str(e)}")


@router.get("/config", response_model=RTCConfigOut)
async def get_rtc_config():
    # Возвращаем STUN серверы
    return RTCConfigOut(
        iceServers=[
            RTCIceServer(urls="stun:stun.l.google.com:19302"),
            RTCIceServer(urls="stun:global.stun.twilio.com:3478"),
        ]
    )