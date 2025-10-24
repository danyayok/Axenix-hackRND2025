from fastapi import FastAPI
from fastapi.responses import ORJSONResponse, RedirectResponse, PlainTextResponse

from app.core.config import settings
from app.api import rooms as rooms_api
from app.api import users as users_api
from app.api import participants as participants_api
from app.db.base import Base
from app.db.session import engine

tags_meta = [
    {"name": "rooms", "description": "Создание, поиск и гостевой доступ в комнаты."},
    {"name": "users", "description": "Профили пользователей (MVP)."},
    {"name": "participants", "description": "Участники комнат: join/leave/heartbeat, список."},
]

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
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
