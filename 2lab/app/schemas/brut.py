from pydantic import BaseModel

class BrutTaskRequest(BaseModel):
    hash: str
    charset: str
    max_length: int

from pydantic import BaseModel

class BrutTaskResponse(BaseModel):
    task_id: int


from typing import Optional
from pydantic import BaseModel

class TaskStatusResponse(BaseModel):
    status: str  # running, completed, failed
    progress: int  # процент выполнения
    result: Optional[str] = None
