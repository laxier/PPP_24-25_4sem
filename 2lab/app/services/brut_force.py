import asyncio
import itertools
import math
from hashlib import sha256

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.models.tasks import Task, TaskStatus

async def run_brut_force(task_id: int, hash_value: str, charset: str, max_length: int):
    async with AsyncSessionLocal() as session:
        # Получаем задачу из базы данных
        task: Task = await session.get(Task, task_id)
        if not task:
            return

        # Вычисляем общее количество комбинаций для расчёта прогресса
        total_combinations = sum(len(charset) ** i for i in range(1, max_length + 1))
        processed = 0
        found_password = None

        # Перебираем все длины пароля от 1 до max_length
        for length in range(1, max_length + 1):
            # Для каждой длины генерируем все комбинации символов
            for candidate in itertools.product(charset, repeat=length):
                candidate_password = ''.join(candidate)
                processed += 1

                # Вычисляем SHA256-хеш для текущего варианта
                candidate_hash = sha256(candidate_password.encode()).hexdigest()
                if candidate_hash == hash_value:
                    found_password = candidate_password
                    break

                if processed % 1000 == 0:
                    progress = math.floor((processed / total_combinations) * 100)
                    task.progress = progress
                    await session.commit()
                    await asyncio.sleep(1)  # даём возможность другим задачам выполняться

            if found_password:
                break

        # Обновляем статус задачи в зависимости от результата
        if found_password:
            task.status = TaskStatus.completed
            task.result = found_password
        else:
            task.status = TaskStatus.failed
            task.result = None

        task.progress = 100
        await session.commit()
