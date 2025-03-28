# import json
# from hashlib import sha256
#
# charset = "abcdefg1234567890"
# max_length = 6
# target_password = "234"
#
#
# # Вычисляем SHA256-хеш пароля
# hash_value = sha256(target_password.encode()).hexdigest()
#
# # Формируем словарь (JSON-объект)
# task_data = {
#     "hash": hash_value,
#     "charset": charset,
#     "max_length": max_length
# }
#
# # Выводим красиво отформатированный JSON
# print("Сгенерированный JSON для теста:\n")
# print(json.dumps(task_data, indent=4))


import json
from hashlib import sha256
import random
import string

# Генерация более сложного пароля
def generate_complex_password(length: int = 8):
    # Пароль может содержать буквы верхнего и нижнего регистра, цифры и спецсимволы
    characters = "ABCDEFG"
    return ''.join(random.choice(characters) for _ in range(length))

# Параметры задачи
charset = "ABCDEFG"  # Расширенный charset
max_length = 5  # Увеличена длина пароля
target_password = generate_complex_password(max_length)  # Генерация более сложного пароля

# Вычисляем SHA256-хеш пароля
hash_value = sha256(target_password.encode()).hexdigest()

# Формируем словарь (JSON-объект)
task_data = {
    "hash": hash_value,
    "charset": charset,
    "max_length": max_length,
    "password": target_password  # Включаем сам сгенерированный пароль
}

# Выводим красиво отформатированный JSON
print("Сгенерированный JSON для теста:\n")
print(json.dumps(task_data, indent=4))
