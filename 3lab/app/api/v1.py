from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
import string
from app.api.deps import CurrentUser
from app.core.security import get_current_user
from app.websocket.manager import manager
from app.celery.tasks import bruteforce_task

router = APIRouter(prefix="/api/v1")

@router.post("/bruteforce")
async def start_bruteforce(
    user: CurrentUser,  # <- должен быть первым
    target_hash: str,
    hash_type: str = "md5",
    max_length: int = 8,
    charset: str = string.ascii_letters + string.digits,
):
    task = bruteforce_task.delay(user.id, target_hash, charset, max_length, hash_type)
    return {"task_id": task.id, "status": "ENQUEUED"}

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: str):
    user = await get_current_user(token=token)
    await manager.connect(ws, user.id)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws, user.id)
