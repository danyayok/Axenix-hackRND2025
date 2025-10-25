# Axenix Conference — Backend (FastAPI)

Бэкенд для онлайн-конференций: комнаты, участники, WebRTC-сигналинг, чат (в т.ч. шифрованный), синхронизация событий, модерация, обложки, и записи встреч (Start/Stop c клиентской записью).

## Стек
- Python 3.11+ / FastAPI / Uvicorn  
- SQLAlchemy async + SQLite  
- JWT (гостевой доступ для WS)  
- `cryptography` (RSA-OAEP обёртки ключа комнаты)  
- Статические файлы через Starlette `StaticFiles`

---

## Быстрый старт (Windows / PowerShell)

```powershell
# 1) создать и активировать venv
python -m venv venv
.env\Scripts\Activate.ps1

# 2) поставить зависимости
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3) запустить сервер (создаст таблицы)
uvicorn app.main:app --host 127.0.0.1 --port 8088

# Swagger
# http://127.0.0.1:8088/docs
```

> Если менялась схема БД (мы на SQLite dev), можно обнулить локальную БД:  
> `Remove-Item .xenix.db`

---

## Структура проекта (основное)

```
app/
  api/
    auth.py          # гостевые токены
    chat.py          # история чата (REST)
    covers.py        # обложки конференций (upload/get/delete)
    crypto.py        # ключ комнаты и обмен «обёртками»
    moderation.py    # роли/мьют/видео/кик/право выступления
    participants.py  # join/leave/heartbeat/список
    recordings.py    # загрузка/список/удаление записей
    rooms.py         # CRUD/валидация комнат
    rtc.py           # ICE-конфиг для WebRTC
    state.py         # состояние комнаты (topic/lock/mute_all)
    sync.py          # догруз событий по seq
    ws.py            # WebSocket: signaling/chat/state/media/record.*
  core/...
  db/...
  models/
    room.py, user.py, membership.py, message.py
    event.py         # EventLog (seq)
    crypto.py        # RoomKey/RoomKeyShare
    recording.py     # записи встреч
  repositories/...   # *repo.py — работа с БД
  services/...       # бизнес-логика
static/
  avatars/           # аватарки
  covers/            # обложки
  records/<slug>/    # файлы записей комнат
```

---

## Основные фичи и эндпоинты

### Комнаты и вход
- `POST /api/rooms` — создать комнату (slug, опционально invite_key)  
- `GET /api/rooms/{slug}` — получить  
- `POST /api/auth/guest` — выдать гостевой JWT для подключения к WS

### Участники и роли
- `GET /api/participants/{slug}` — список участников, статусы  
- `POST /api/moderation/{slug}/promote_admin|demote_admin` — роль admin  
- `POST /api/moderation/{slug}/kick` — кик  
- `POST /api/moderation/{slug}/force_mute` — принудительный mute  
- `POST /api/moderation/{slug}/force_video` — принудительно выключить видео  
- `POST /api/moderation/{slug}/speak` — выдать/снять право выступления (обход `mute_all`)

### Состояние комнаты
- `POST /api/state/{slug}/set_topic|set_lock|set_mute_all`  
- В `state.snapshot` в WS приходит: `topic`, `is_locked`, `mute_all`, `recording_active`, `hands_up`

### WebRTC (сигналинг по WS)
- Вход/подписка: `GET /ws/rooms/{slug}?token=...&invite_key=...`  
- Сообщения: `offer`, `answer`, `ice` (адресно `to`)  
- Сам медиапоток между клиентами (P2P/SFU) — вне бэкенда

### Медиа-состояние / руки (WS)
- `media.self { mic_muted, cam_off }` → `media.updated` (бродкаст)  
- `hand.raise / hand.lower` → события

### Чат
- **REST**: `GET /api/chat/{slug}?limit=&before_id=` — история  
- **WS**: `chat.message { text }` (rate-limit, фильтр) → бродкаст  
- **WS**: `chat.typing { is_typing }` — индикатор набора

### Синхронизация (seq)
- **REST**: `GET /api/sync/{slug}?after_seq=` — догруз событий  
- **WS**: `sync.sub { after_seq }` → `sync.batch`  
- Все важные WS-события содержат `seq`; при входе приходит `sync.info { next_seq }`

### Шифрование (MVP)
- Публичный ключ в профиле: `PATCH /api/users/{id} { public_key_pem }`  
- Сгенерировать ключ комнаты (AES-256-GCM) + раздать «обёртки» (RSA-OAEP):
  - `POST /api/crypto/{slug}/init?actor_user_id=...`
- Забрать свою «обёртку»:
  - `GET /api/crypto/{slug}/my_key?user_id=...`
- Шифр-чат (WS, сервер не видит plaintext):  
  `chat.message.enc { algo, ciphertext_b64 }`

### Обложки конференций
- `POST /api/covers/{slug}/upload?actor_user_id=...` (multipart `file`)  
- `GET /api/covers/{slug}` → `{ cover_url }`  
- `DELETE /api/covers/{slug}?actor_user_id=...`

### Записи встреч (Start/Stop на фронте, запись делает клиент)
- **WS**:
  - Start: `{"type":"record.start"}` (owner/admin) → бродкаст `record.started` + `recording_active=true`
  - Stop:  `{"type":"record.stop"}`  (owner/admin) → бродкаст `record.stopped` + `recording_active=false`
- **Upload (REST)**: `POST /api/recordings/{slug}/upload?uploader_user_id=...`  
  (multipart: `file`, form: `title`, `duration_sec`)  
  сохраняется в `static/records/<slug>/`
- **List/Delete**:
  - `GET /api/recordings/{slug}`
  - `DELETE /api/recordings/{slug}/{rec_id}?actor_user_id=...`

---

## WebSocket протокол (кратко)

Сразу после подключения приходят:
```json
joined,
state.snapshot { "topic": "...", "is_locked": false, "mute_all": false, "recording_active": false, "hands_up": [] },
sync.info { "next_seq": 1 }
```

Далее важные типы:
- signaling: `offer | answer | ice`
- chat: `chat.message`, `chat.message.enc`, `chat.typing`
- participants: `member.joined`, `member.left`, `role.changed`, `member.kicked`
- media/state: `media.updated`, `state.changed`, `hand.raised/lowered`
- moderation: `media.forced`, `media.video_forced`
- recording: `record.started`, `record.stopped`
- sync: `sync.batch` (по запросу `sync.sub`)
- ошибки: `{ "type": "error", "reason": "..." }`  
- почти все бродкасты содержат `seq`

---

## Roadmap (что можно добавить дальше)

- Серверная запись (через SFU/медиасервер).
- Ротация ключа комнаты, X25519 ECDH, forward secrecy.
- ACL на скачивание записей, TTL и физическое удаление.
- Ограничения на тип/размер загружаемых файлов.
- Больше метрик и алертов.
