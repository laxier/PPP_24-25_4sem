from celery import Celery
from app.core.settings import get_settings

settings = get_settings()

celery = Celery(
    "bruteforce",
    broker=settings.broker_url,
    backend=settings.result_backend,
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)
