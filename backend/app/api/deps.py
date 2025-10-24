from collections.abc import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.repositories.room_repo import RoomRepository
from app.services.rooms import RoomService

# Глобальный автокоммит на каждый успешный запрос REST.
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()       # commit на успехе
        except Exception:
            await session.rollback()     # rollback на ошибке
            raise

# Оставляем DI-хелперы как были (если где-то используются)
async def get_room_repo(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[RoomRepository, None]:
    yield RoomRepository(db)

async def get_room_service(repo: RoomRepository = Depends(get_room_repo)) -> AsyncGenerator[RoomService, None]:
    yield RoomService(repo)
