# app/celery/tasks.py
import itertools, time, hashlib, json
from datetime import timedelta
from celery import Celery
import redis

from app.core.celery_app import celery

# создаём синхронный клиент Redis — он используется только внутри Celery
redis_client = redis.Redis(host="localhost", port=6380, db=0)

def publish_status(user_id: int, message: dict):
    channel = f"ws_{user_id}"
    redis_client.publish(channel, json.dumps(message))

@celery.task(bind=True)
def bruteforce_task(self, user_id: int, target_hash: str,
                    charset: str, max_len: int, hash_type: str = "md5"):

    print(f"🔧 Task {self.request.id} started for user {user_id}")
    algo = getattr(hashlib, hash_type)
    start = time.perf_counter()

    for length in range(1, max_len + 1):
        for chars in itertools.product(charset, repeat=length):
            guess = "".join(chars)
            if algo(guess.encode()).hexdigest() == target_hash:
                elapsed = str(timedelta(seconds=int(time.perf_counter() - start)))
                print(f"✅ Found {guess} in {elapsed}")
                publish_status(user_id, {
                    "status": "COMPLETED",
                    "task_id": self.request.id,
                    "result": guess,
                    "elapsed_time": elapsed,
                })
                return guess

    print("❌ Not found")
    publish_status(user_id, {
        "status": "FAILED",
        "task_id": self.request.id,
        "message": "Password not found",
    })
    return ""
