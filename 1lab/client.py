#!/usr/bin/env python3
"""
File Manager Client.

Клиент подключается к серверу и позволяет отправлять команды:
  - add <имя_программы>    : Создать и запустить программу.
  - start <имя_программы>  : Запустить программу, если она не запущена.
  - stop <имя_программы>   : Остановить запущенную программу.
  - delete <имя_программы> : Удалить программу и её логи.
  - getlog <имя_программы> : Получить логи указанной программы.
  - exit                 : Завершить работу клиента.
"""

import socket
import argparse


def main():
    """
    Парсит аргументы командной строки, устанавливает соединение с сервером,
    и позволяет пользователю отправлять команды.
    """
    parser = argparse.ArgumentParser(description="File Manager Client")
    parser.add_argument('--host', type=str, default='127.0.0.1',
                        help="IP-адрес сервера (по умолчанию: 127.0.0.1)")
    parser.add_argument('--port', type=int, default=54321,
                        help="Порт сервера (по умолчанию: 54321)")
    args = parser.parse_args()

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((args.host, args.port))
        print(f"Подключено к серверу {args.host}:{args.port}")
    except Exception as e:
        print(f"Не удалось подключиться к серверу: {e}")
        return

    print("Доступные команды:")
    print("  add <имя_программы>    - создать и запустить программу")
    print("  start <имя_программы>  - запустить программу, если она не запущена")
    print("  stop <имя_программы>   - остановить запущенную программу")
    print("  delete <имя_программы> - удалить программу и её логи")
    print("  getlog <имя_программы> - получить логи указанной программы")
    print("  exit                 - завершить работу клиента")

    try:
        while True:
            command = input("Введите команду: ").strip()
            if not command:
                continue
            if command.lower() == "exit":
                print("Завершение работы клиента.")
                break

            try:
                client_socket.send(command.encode('utf-8'))
                response = client_socket.recv(4096)
                if not response:
                    print("Соединение закрыто сервером.")
                    break
                print("Ответ сервера:")
                print(response.decode('utf-8'))
            except Exception as e:
                print(f"Ошибка при отправке команды: {e}")
                break
    finally:
        client_socket.close()


if __name__ == '__main__':
    main()
