import aiohttp
import asyncio
import json

BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/api/v1/ws"

async def send_bruteforce_request(target_hash: str, charset: str, max_length: int, hash_type: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/api/v1/bruteforce",
            json={
                "target_hash": target_hash,
                "charset": charset,
                "max_length": max_length,
                "hash_type": hash_type
            }
        ) as response:
            if response.status != 200:
                print("❌ Ошибка запуска задачи:", await response.text())
                return None
            data = await response.json()
            print("🚀 Задача отправлена:", data)
            return data

async def listen_ws():
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(WS_URL) as ws:
            print("📡 Подключено к WebSocket. Ожидание результатов...")
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        print("📨 Уведомление:", json.dumps(data, indent=2))
                    except json.JSONDecodeError:
                        print("🔸 Сообщение:", msg.data)
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    print("🔌 WebSocket закрыт.")
                    break

async def main():
    print("=== Запуск брутфорса ===")
    target_hash = input("Введите хеш: ")
    charset = input("Допустимые символы (по умолчанию: abc123): ") or "abc123"
    max_length = int(input("Максимальная длина пароля (по умолчанию: 6): ") or 6)
    hash_type = input("Тип хеша (по умолчанию: md5): ") or "md5"

    await send_bruteforce_request(target_hash, charset, max_length, hash_type)
    await listen_ws()

if __name__ == "__main__":
    asyncio.run(main())
