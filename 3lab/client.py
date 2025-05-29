from app.celery.tasks import bruteforce_task

# Пример параметров
target_hash = "25d55ad283aa400af464c76d713c07ad"
charset = "0123456789"
max_length = 8
hash_type = "md5"
user_id = 0  # если требуется

# Отправка задачи в очередь
result = bruteforce_task.delay(user_id, target_hash, charset, max_length, hash_type)

# Печать task_id
print(f"Task sent! ID: {result.id}")
