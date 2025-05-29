from celery import Celery
from app.core.settings import get_settings

settings = get_settings()

# app/core/celery_app.py

from celery import Celery

celery = Celery(
    "bruteforce",
    broker="redis://localhost:6380/0",
    backend="redis://localhost:6380/0"
)

celery.autodiscover_tasks(["app.celery"])

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)
