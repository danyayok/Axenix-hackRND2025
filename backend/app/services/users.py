from app.repositories.user_repo import UserRepository
from app.models.user import User

class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def create_user(self, *, nickname: str, avatar_url: str | None) -> User:
        return await self.repo.create(nickname=nickname, avatar_url=avatar_url)
