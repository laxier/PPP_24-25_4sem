import aiohttp
import asyncio
import json

BASE_URL = "http://127.0.0.1:8000"
USER_ID = 1
WS_URL = f"ws://127.0.0.1:8000/api/v1/ws/{USER_ID}"

async def send_bruteforce_request(target_hash, charset, max_length, hash_type):
    payload = {
        "user_id": USER_ID,
        "target_hash": target_hash,
        "charset": charset,
        "max_length": max_length,
        "hash_type": hash_type
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE_URL}/api/v1/bruteforce", json=payload) as resp:
            if resp.status != 200:
                text = await resp.text()
                print("❌ Ошибка запуска задачи:", text)
                return
            data = await resp.json()
            print("🚀 Задача отправлена:", data)

async def listen_ws():
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(WS_URL) as ws:
            print("📡 WebSocket подключён, ждём результат...")
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    print("📨 Уведомление:", msg.data)
                else:
                    break

async def main():
    print("=== Запуск брутфорса ===")
    target_hash = input("Хеш: ")
    charset = input("Символы (дефолт abc123456): ") or "abc123456"
    max_length = int(input("Макс длина (дефолт 6): ") or 6)
    hash_type = input("Тип хеша (дефолт md5): ") or "md5"

    await send_bruteforce_request(target_hash, charset, max_length, hash_type)
    await listen_ws()

if __name__ == "__main__":
    asyncio.run(main())
