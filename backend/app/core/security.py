import time
import jwt
from typing import Optional, Dict, Any
from app.core.config import settings
import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(*, user_id: int, extra: Optional[Dict[str, Any]] = None, ttl: Optional[int] = None) -> str:
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + int(ttl or settings.jwt_ttl_seconds),
        "uid": user_id,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])

def get_user_id_from_token(token: str) -> int:
    data = decode_token(token)
    uid = data.get("uid")
    if not isinstance(uid, int):
        # на всякий случай поддержим строку
        try:
            uid = int(str(uid))
        except Exception:
            raise ValueError("invalid_token_uid")
    return uid
