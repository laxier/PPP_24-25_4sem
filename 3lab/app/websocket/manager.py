from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"✅ User {user_id} connected via WebSocket")

    def disconnect(self, user_id: int):
        self.active_connections.pop(user_id, None)
        print(f"❌ User {user_id} disconnected")

    async def send_json(self, user_id: int, message: dict):
        ws = self.active_connections.get(user_id)
        if ws:
            try:
                await ws.send_json(message)
                print(f"📤 Sent to {user_id}: {message}")
            except Exception as e:
                print(f"⚠️ WebSocket send error for user {user_id}: {e}")
        else:
            print(f"🚫 No WebSocket for user {user_id}, cannot send: {message}")

manager = ConnectionManager()
