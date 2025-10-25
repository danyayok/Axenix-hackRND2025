import re

MAX_LEN = 2000
BADWORDS = {"хуй","пизд","еба","сука","бля","fuck","shit"}  # простейший список, мatch по подстроке

_ws_re = re.compile(r"\s+")

def sanitize_message(raw: str) -> str:
    if raw is None:
        return ""
    s = raw.replace("\r", " ").replace("\n", " ").strip()
    s = _ws_re.sub(" ", s)
    if len(s) > MAX_LEN:
        s = s[:MAX_LEN]
    return s

def has_bad_words(s: str) -> bool:
    low = s.lower()
    return any(w in low for w in BADWORDS)
