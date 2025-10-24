import secrets
import string
import re

_slug_safe = string.ascii_lowercase + string.digits

def gen_slug(n: int = 8) -> str:
    return ''.join(secrets.choice(_slug_safe) for _ in range(n))

def gen_invite_key(n: int = 22) -> str:
    # URL-safe ключ приглашения
    return secrets.token_urlsafe(n)

def normalize_title_to_slug_hint(title: str) -> str:
    s = title.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:40]
