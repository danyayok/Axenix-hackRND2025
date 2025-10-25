import os, base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from app.repositories.crypto_repo import CryptoRepository
from app.repositories.room_repo import RoomRepository
from app.repositories.membership_repo import MembershipRepository
from app.repositories.user_repo import UserRepository

class CryptoService:
    def __init__(self, rrepo: RoomRepository, mrepo: MembershipRepository, urepo: UserRepository, crepo: CryptoRepository):
        self.rrepo = rrepo
        self.mrepo = mrepo
        self.urepo = urepo
        self.crepo = crepo

    async def _room_ctx(self, slug: str):
        room = await self.rrepo.get_by_slug(slug)
        if not room:
            raise ValueError("room_not_found")
        return room

    async def init_room_key(self, *, room_slug: str, actor_user_id: int) -> dict:
        room = await self._room_ctx(room_slug)
        m = await self.mrepo.get_active(room_id=room.id, user_id=actor_user_id)
        role = m.role if m else "guest"
        if role not in ("owner", "admin"):
            raise ValueError("forbidden")

        # 32 байта AES ключа
        aes_key = os.urandom(32)
        rk = await self.crepo.create_room_key(room_id=room.id, created_by=actor_user_id, algo="AES-256-GCM")

        participants = await self.mrepo.list_by_room(room_id=room.id, limit=500)
        wrapped_count = 0
        for mem in participants:
            user = await self.urepo.get(mem.user_id)
            if not user or not user.public_key_pem:
                continue
            try:
                pub = serialization.load_pem_public_key(user.public_key_pem.encode("utf-8"))
                wrapped = pub.encrypt(
                    aes_key,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None,
                    ),
                )
                b64 = base64.b64encode(wrapped).decode("ascii")
                await self.crepo.add_share(room_key_id=rk.id, room_id=room.id, user_id=user.id, wrapped_key_b64=b64)
                wrapped_count += 1
            except Exception:
                # некорректный публичный ключ пользователя — пропускаем
                continue

        return {"room_key_id": rk.id, "algo": rk.algo, "distributed": wrapped_count}

    async def get_my_wrapped_key(self, *, room_slug: str, user_id: int) -> dict | None:
        room = await self._room_ctx(room_slug)
        sh = await self.crepo.latest_share_for_user(room_id=room.id, user_id=user_id)
        if not sh:
            return None
        return {"algo": "AES-256-GCM", "wrapped_key_b64": sh.wrapped_key_b64}
