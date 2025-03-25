from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.brut import BrutTaskRequest, BrutTaskResponse, TaskStatusResponse
from app.db.session import AsyncSessionLocal
from app.models.tasks import Task, TaskStatus
from app.services.brut_force import run_brut_force
from sqlalchemy.future import select

router = APIRouter()


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/brut_hash", response_model=BrutTaskResponse)
async def brut_hash(
        request: BrutTaskRequest,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db)
):
    if request.max_length > 8:
        raise HTTPException(status_code=400, detail="max_length не должен превышать 8")

    # Создаём новую задачу в базе данных
    new_task = Task(
        hash_value=request.hash,  # или request.hash_value, если так определено в схеме
        charset=request.charset,
        max_length=request.max_length,
        status=TaskStatus.running,
        progress=0,
        result=None
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    # Добавляем фоновую задачу, которая выполнит брутфорс и обновит задачу в БД
    background_tasks.add_task(
        run_brut_force,
        new_task.id,  # передаём ID задачи из БД
        request.hash,  # хеш, который надо перебрать
        request.charset,  # словарь символов
        request.max_length
    )

    return BrutTaskResponse(task_id=new_task.id)


@router.get("/get_status", response_model=TaskStatusResponse)
async def get_status(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Формируем ответ. Если TaskStatus является enum, можно вернуть его значение.
    return TaskStatusResponse(
        status=task.status.value if isinstance(task.status, TaskStatus) else task.status,
        progress=task.progress,
        result=task.result
    )
