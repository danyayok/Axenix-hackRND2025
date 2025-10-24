from __future__ import annotations
import asyncio
from typing import Dict, Set
from fastapi import WebSocket

class RoomHub:
    """Хранит WebSocket-подключения в одной комнате."""
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self.members: Dict[int, WebSocket] = {}  # user_id -> ws

    async def add(self, user_id: int, ws: WebSocket) -> None:
        async with self._lock:
            self.members[user_id] = ws

    async def remove(self, user_id: int) -> None:
        async with self._lock:
            self.members.pop(user_id, None)

    async def send_to(self, user_id: int, data: dict) -> None:
        ws = self.members.get(user_id)
        if not ws:
            return
        try:
            await ws.send_json(data)
        except Exception:
            # клиент мог отвалиться
            await self.remove(user_id)

    async def broadcast(self, data: dict, exclude: Set[int] | None = None) -> None:
        targets = []
        async with self._lock:
            for uid, ws in self.members.items():
                if exclude and uid in exclude:
                    continue
                targets.append(ws)
        # отправляем параллельно
        await asyncio.gather(*[t.send_json(data) for t in targets], return_exceptions=True)

class WsHub:
    """Держит хабы всех комнат, ленивая выдача."""
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self.rooms: Dict[str, RoomHub] = {}

    async def _get_room(self, room_slug: str) -> RoomHub:
        async with self._lock:
            hub = self.rooms.get(room_slug)
            if not hub:
                hub = RoomHub()
                self.rooms[room_slug] = hub
            return hub

    async def join(self, room_slug: str, user_id: int, ws: WebSocket) -> None:
        hub = await self._get_room(room_slug)
        await hub.add(user_id, ws)

    async def leave(self, room_slug: str, user_id: int) -> None:
        hub = await self._get_room(room_slug)
        await hub.remove(user_id)

    async def send_to(self, room_slug: str, to_user_id: int, data: dict) -> None:
        hub = await self._get_room(room_slug)
        await hub.send_to(to_user_id, data)

    async def broadcast(self, room_slug: str, data: dict, exclude: set[int] | None = None) -> None:
        hub = await self._get_room(room_slug)
        await hub.broadcast(data, exclude=exclude)

HUB = WsHub()
