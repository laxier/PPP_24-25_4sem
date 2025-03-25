import enum
from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.models import Base

class TaskStatus(enum.Enum):
    running = "running"
    completed = "completed"
    failed = "failed"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    hash_value = Column(String, nullable=False)     # хеш RAR-архива
    charset = Column(String, nullable=False)          # словарь символов
    max_length = Column(Integer, nullable=False)      # максимальная длина пароля
    status = Column(Enum(TaskStatus), default=TaskStatus.running, nullable=False)
    progress = Column(Integer, default=0, nullable=False)
    result = Column(String, nullable=True)            # найденный пароль или null
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # если нужна привязка к пользователю

    user = relationship("User", back_populates="tasks")
