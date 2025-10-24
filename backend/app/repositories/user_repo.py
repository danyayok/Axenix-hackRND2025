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

    async def update_avatar_url(self, user_id: int, avatar_url: str) -> Optional[User]:
        user = await self.get(user_id)
        if not user:
            return None
        user.avatar_url = avatar_url
        await self.session.flush()
        await self.session.refresh(user)
        return user
