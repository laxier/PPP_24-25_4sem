import asyncio
import itertools
import math
from hashlib import sha256

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.models.tasks import Task, TaskStatus

# чистая sync-функция (CPU-heavy)
import itertools
from hashlib import sha256

def brut_force_sync(hash_value: str, charset: str, max_length: int):
    total = sum(len(charset) ** i for i in range(1, max_length + 1))
    processed = 0

    for length in range(1, max_length + 1):
        for candidate in itertools.product(charset, repeat=length):
            processed += 1
            candidate_password = ''.join(candidate)
            candidate_hash = sha256(candidate_password.encode()).hexdigest()

            if candidate_hash == hash_value:
                return {
                    "found": True,
                    "password": candidate_password,
                    "processed": processed,
                    "total": total,
                }

    return {
        "found": False,
        "password": None,
        "processed": processed,
        "total": total,
    }

import asyncio
from concurrent.futures import ProcessPoolExecutor

async def run_brut_force(task_id: int, hash_value: str, charset: str, max_length: int):
    async with AsyncSessionLocal() as session:
        task: Task = await session.get(Task, task_id)
        if not task:
            return

        # Обновляем статус
        task.status = TaskStatus.running
        task.progress = 0
        await session.commit()

    # Запускаем sync-брутфорс в другом процессе
    loop = asyncio.get_event_loop()
    with ProcessPoolExecutor() as executor:
        result = await loop.run_in_executor(
            executor,
            brut_force_sync,
            hash_value, charset, max_length
        )

    # Сохраняем результат в базу
    async with AsyncSessionLocal() as session:
        task: Task = await session.get(Task, task_id)
        if result["found"]:
            task.status = TaskStatus.completed
            task.result = result["password"]
        else:
            task.status = TaskStatus.failed
            task.result = None

        task.progress = 100
        await session.commit()
