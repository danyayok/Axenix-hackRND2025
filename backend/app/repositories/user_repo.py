from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, *, nickname: str, avatar_url: str | None) -> User:
        user = User(nickname=nickname, avatar_url=avatar_url)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def get(self, user_id: int) -> Optional[User]:
        q = await self.session.execute(select(User).where(User.id == user_id))
        return q.scalar_one_or_none()
