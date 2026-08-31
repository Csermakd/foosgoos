"""
Websocket fan-out for live match updates.

The frontend opens one socket per match and receives every goal event as
it lands, whether it came from a human tapping a button on another device
or from the camera. Kept deliberately dumb: no auth, no reconnection
bookkeeping, no message history. A client that misses messages re-syncs
by GETting /matches/{id} , which is the source of truth.
"""
import asyncio
from typing import Dict, Set

from fastapi import WebSocket


class MatchConnectionManager:
    def __init__(self):
        self._rooms: Dict[int, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, match_id: int, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self._rooms.setdefault(match_id, set()).add(websocket)

    async def disconnect(self, match_id: int, websocket: WebSocket):
        async with self._lock:
            room = self._rooms.get(match_id)
            if not room:
                return
            room.discard(websocket)
            if not room:
                self._rooms.pop(match_id, None)

    async def broadcast(self, match_id: int, message: dict):
        """Send to everyone watching this match. Dead sockets are dropped
        rather than raised - a browser tab closing must never be able to
        fail the HTTP request that triggered the broadcast."""
        async with self._lock:
            targets = list(self._rooms.get(match_id, ()))

        dead = []
        for ws in targets:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)

        for ws in dead:
            await self.disconnect(match_id, ws)

    def connection_count(self, match_id: int) -> int:
        return len(self._rooms.get(match_id, ()))


manager = MatchConnectionManager()
