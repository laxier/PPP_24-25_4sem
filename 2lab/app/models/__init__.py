from sqlalchemy.orm import declarative_base

Base = declarative_base()

from app.models.user import User
from app.models.token import Token
from app.models.tasks import Task
