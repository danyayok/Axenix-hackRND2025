from fastapi import FastAPI
from fastapi.responses import ORJSONResponse, RedirectResponse, PlainTextResponse

from app.core.config import settings
from app.api import rooms as rooms_api
from app.db.base import Base
from app.db.session import engine

tags_meta = [
    {"name": "rooms", "description": "Создание, поиск и гостевой доступ в комнаты."},
]

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    default_response_class=ORJSONResponse,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_meta,
)

@app.on_event("startup")
async def on_startup() -> None:
    # Автосоздание таблиц в SQLite (MVP без Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return PlainTextResponse("", status_code=204)

# REST: /api/rooms/*
app.include_router(rooms_api.router, prefix="/api/rooms", tags=["rooms"])
