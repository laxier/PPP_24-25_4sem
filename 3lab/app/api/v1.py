from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import string
from app.websocket.manager import manager
from app.celery.tasks import bruteforce_task

router = APIRouter(prefix="/api/v1")

@router.post("/bruteforce")
async def start_bruteforce(
    target_hash: str,
    hash_type: str = "md5",
    max_length: int = 8,
    charset: str = string.ascii_letters + string.digits,
):
    # Просто ставим user_id как 0 или любой другой, если он обязателен
    task = bruteforce_task.delay(0, target_hash, charset, max_length, hash_type)
    return {"task_id": task.id, "status": "ENQUEUED"}

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    # Не проверяем токен, не достаём пользователя
    fake_user_id = 0
    await manager.connect(ws, fake_user_id)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws, fake_user_id)


from celery.result import AsyncResult
from fastapi import HTTPException

@router.get("/bruteforce/{task_id}")
async def get_task_status(task_id: str):
    result = AsyncResult(task_id)
    if result.state == "PENDING":
        return {"status": "PENDING"}
    elif result.state == "STARTED":
        return {"status": "STARTED"}
    elif result.state == "SUCCESS":
        return {"status": "SUCCESS", "result": result.result}
    elif result.state == "FAILURE":
        return {"status": "FAILURE", "error": str(result.result)}
    else:
        return {"status": result.state}
