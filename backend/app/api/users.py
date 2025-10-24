from fastapi import APIRouter, Depends
from starlette.status import HTTP_201_CREATED
from app.api.deps import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repo import UserRepository
from app.services.users import UserService
from app.schemas.user import UserCreate, UserOut

router = APIRouter()

def _svc(db: AsyncSession) -> UserService:
    return UserService(UserRepository(db))

@router.post("", response_model=UserOut, status_code=HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> UserOut:
    u = await _svc(db).create_user(nickname=payload.nickname, avatar_url=payload.avatar_url)
    return UserOut.model_validate(u)
