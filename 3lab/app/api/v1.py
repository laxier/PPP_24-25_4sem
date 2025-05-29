from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import string
from app.websocket.manager import manager
from app.celery.tasks import bruteforce_task

router = APIRouter(prefix="/api/v1")

from pydantic import BaseModel

class BruteforceRequest(BaseModel):
    user_id: int
    target_hash: str
    charset: str = "abcdefghijklmnopqrstuvwxyz0123456789"
    max_length: int = 8
    hash_type: str = "md5"


@router.post("/bruteforce")
async def start_bruteforce(data: BruteforceRequest):
    task = bruteforce_task.delay(
        data.user_id,
        data.target_hash,
        data.charset,
        data.max_length,
        data.hash_type
    )
    return {"task_id": task.id, "status": "ENQUEUED"}

# app/api/v1/routes.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import aioredis

# from app.websocket.manager import manager  # manager теперь просто для connect/disconnect


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(ws: WebSocket, user_id: int):
    await manager.connect(ws, user_id)

    # создаём асинхронный Redis и подписываемся
    redis = await aioredis.create_redis("redis://localhost:6379/0")
    channel, = await redis.subscribe(f"ws_{user_id}")

    try:
        while True:
            # ждём публикацию от Celery
            msg = await channel.get(encoding="utf-8")
            await ws.send_text(msg)
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    finally:
        await redis.unsubscribe(f"ws_{user_id}")
        redis.close()
        await redis.wait_closed()



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
