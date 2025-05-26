import itertools, string, time, hashlib
from datetime import timedelta
from app.core.celery_app import celery
from app.websocket.manager import manager

@celery.task(bind=True)
def bruteforce_task(self, user_id: int, target_hash: str,
                    charset: str, max_len: int, hash_type: str = "md5"):

    algo = getattr(hashlib, hash_type)
    combos = 0
    start = time.perf_counter()

    manager.send_json(user_id, {
        "status": "STARTED",
        "task_id": self.request.id,
        "hash_type": hash_type,
        "charset_length": len(charset),
        "max_length": max_len,
    })

    for length in range(1, max_len + 1):
        for chars in itertools.product(charset, repeat=length):
            guess = ''.join(chars)
            combos += 1

            if combos % 10_000 == 0:
                elapsed = time.perf_counter() - start
                progress = int((length / max_len) * 100)
                cps = int(combos / elapsed)
                manager.send_json(user_id, {
                    "status": "PROGRESS",
                    "task_id": self.request.id,
                    "progress": progress,
                    "current_combination": guess,
                    "combinations_per_second": cps,
                })

            if algo(guess.encode()).hexdigest() == target_hash:
                manager.send_json(user_id, {
                    "status": "COMPLETED",
                    "task_id": self.request.id,
                    "result": guess,
                    "elapsed_time": str(timedelta(seconds=int(time.perf_counter() - start))),
                })
                return guess

    manager.send_json(user_id, {
        "status": "FAILED",
        "task_id": self.request.id,
        "message": "Password not found",
    })
    return ""
