from typing import Dict, Set
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active: Dict[int, Set[WebSocket]] = {}

    async def connect(self, ws: WebSocket, user_id: int):
        await ws.accept()
        self.active.setdefault(user_id, set()).add(ws)

    def disconnect(self, ws: WebSocket, user_id: int):
        self.active[user_id].remove(ws)
        if not self.active[user_id]:
            del self.active[user_id]

    async def send_json(self, user_id: int, msg: dict):
        for ws in self.active.get(user_id, []):
            await ws.send_json(msg)

manager = ConnectionManager()
