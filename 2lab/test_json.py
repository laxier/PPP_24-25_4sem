import json
from hashlib import sha256

charset = "abcdefg1234567890"
max_length = 6
target_password = "234"


# Вычисляем SHA256-хеш пароля
hash_value = sha256(target_password.encode()).hexdigest()

# Формируем словарь (JSON-объект)
task_data = {
    "hash": hash_value,
    "charset": charset,
    "max_length": max_length
}

# Выводим красиво отформатированный JSON
print("Сгенерированный JSON для теста:\n")
print(json.dumps(task_data, indent=4))
