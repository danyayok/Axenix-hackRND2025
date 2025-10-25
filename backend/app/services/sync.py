import json
from typing import Sequence
from app.repositories.event_repo import EventRepository
from app.repositories.room_repo import RoomRepository
from app.models.event import EventLog

class SyncService:
    def __init__(self, r_repo: RoomRepository, e_repo: EventRepository):
        self.r_repo = r_repo
        self.e_repo = e_repo

    async def _room_id(self, room_slug: str) -> int:
        room = await self.r_repo.get_by_slug(room_slug)
        if not room:
            raise ValueError("room_not_found")
        return room.id

    async def append(self, *, room_slug: str, type_: str, payload: dict) -> EventLog:
        room_id = await self._room_id(room_slug)
        ev = await self.e_repo.append(room_id=room_id, type_=type_, payload_json=json.dumps(payload, ensure_ascii=False))
        return ev

    async def list_after(self, *, room_slug: str, after_seq: int, limit: int = 200) -> list[dict]:
        room_id = await self._room_id(room_slug)
        events = await self.e_repo.list_after(room_id=room_id, after_seq=after_seq, limit=limit)
        out: list[dict] = []
        for e in events:
            try:
                payload = json.loads(e.payload)
            except Exception:
                payload = {"raw": e.payload}
            out.append({"seq": e.id, "type": e.type, "payload": payload, "created_at": e.created_at.isoformat() + "Z"})
        return out

    async def next_seq(self) -> int:
        return await self.e_repo.next_seq()
