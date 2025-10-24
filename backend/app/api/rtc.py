from fastapi import APIRouter
from app.core.config import settings
from app.schemas.rtc import RTCConfigOut, RTCIceServer

router = APIRouter()

@router.get("/config", response_model=RTCConfigOut)
async def get_rtc_config() -> RTCConfigOut:
    servers = [RTCIceServer(urls=settings.stun_url)]
    if settings.turn_url and settings.turn_username and settings.turn_password:
        servers.append(
            RTCIceServer(
                urls=settings.turn_url,
                username=settings.turn_username,
                credential=settings.turn_password,
            )
        )
    return RTCConfigOut(iceServers=servers)
