from fastapi import FastAPI
from fastapi.responses import ORJSONResponse, RedirectResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.config import settings
from app.api import rooms as rooms_api
from app.api import users as users_api
from app.api import participants as participants_api
from app.api import chat as chat_api
from app.api import state as state_api
from app.api import auth as auth_api
from app.api import rtc as rtc_api
from app.api import moderation as moderation_api
from app.api import sync as sync_api
from app.api import crypto as crypto_api
from app.api import ws as ws_api
from app.db.base import Base
from app.db.session import engine

Path("static/avatars").mkdir(parents=True, exist_ok=True)

tags_meta = [
    {"name": "rooms", "description": "Создание, поиск и гостевой доступ в комнаты."},
    {"name": "users", "description": "Профили пользователей (MVP)."},
    {"name": "participants", "description": "Участники комнат: join/leave/heartbeat, список."},
    {"name": "chat", "description": "История сообщений и real-time через WS."},
    {"name": "state", "description": "Состояние комнаты: topic/lock/mute_all, поднятые руки."},
    {"name": "auth", "description": "Гостевые токены (JWT) для подключения к WS."},
    {"name": "rtc", "description": "ICE-конфигурация (STUN/TURN) для WebRTC."},
    {"name": "moderation", "description": "Роли (owner/admin/guest), kick и принудительный mute."},
    {"name": "sync", "description": "Синхронизация событий комнаты (sequence + догруз)."},
    {"name": "crypto", "description": "Ключ комнаты и обмен обёртками (RSA-OAEP), шифр-чат."},
]

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    default_response_class=ORJSONResponse,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_meta,
)

@app.on_event("startup")
async def on_startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return PlainTextResponse("", status_code=204)

# REST
app.include_router(rooms_api.router,        prefix="/api/rooms",        tags=["rooms"])
app.include_router(users_api.router,        prefix="/api/users",        tags=["users"])
app.include_router(participants_api.router, prefix="/api/participants", tags=["participants"])
app.include_router(chat_api.router,         prefix="/api/chat",         tags=["chat"])
app.include_router(state_api.router,        prefix="/api/state",        tags=["state"])
app.include_router(auth_api.router,         prefix="/api/auth",         tags=["auth"])
app.include_router(rtc_api.router,          prefix="/api/rtc",          tags=["rtc"])
app.include_router(moderation_api.router,   prefix="/api/moderation",   tags=["moderation"])
app.include_router(sync_api.router,         prefix="/api/sync",         tags=["sync"])
app.include_router(crypto_api.router,       prefix="/api/crypto",       tags=["crypto"])

# WS
app.include_router(ws_api.router)

app.mount("/static", StaticFiles(directory="static"), name="static")
