2. Запустить FastAPI

python -m uvicorn main:app --reload
Открой: http://127.0.0.1:8000/docs

3. Запустить Celery worker

python -m celery -A app.core.celery_app.celery worker -l info


Брутфорс-задача должна выполняться в фоновом режиме, параллельно с FastAPI, чтобы не блокировать основной сервер.