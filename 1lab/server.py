#!/usr/bin/env python3
"""
File Manager Server.

Поддерживает следующие команды, получаемые от клиента:
  - add <имя_программы>    : Создать (если отсутствует) и запустить программу.
  - start <имя_программы>  : Запустить программу, если она уже существует, но не запущена.
  - stop <имя_программы>   : Остановить запущенную программу.
  - delete <имя_программы> : Удалить программу и её логи.
  - getlog <имя_программы> : Получить логи указанной программы.
"""

import os
import sys
import time
import json
import socket
import threading
import logging
import signal
import argparse
import shutil
from subprocess import Popen, PIPE

# Настройка логирования сервера
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class ProgramRunner(threading.Thread):
    """
    Класс для циклического запуска программы и записи её логов.

    Атрибуты:
        prog_name (str): Имя файла программы.
        interval (int): Интервал между запусками.
        state (dict): Общая структура состояния (для хранения путей к логам).
        running (bool): Флаг, контролирующий работу цикла.
    """

    def __init__(self, prog_name, interval, state):
        super().__init__(daemon=True)
        self.prog_name = prog_name
        self.interval = interval
        self.state = state
        self.running = True

    def run(self):
        """
        Запускает цикл, в котором программа запускается с заданным интервалом,
        а её вывод сохраняется в отдельную папку для логов.
        """
        log_dir = f"{self.prog_name}_logs"
        os.makedirs(log_dir, exist_ok=True)
        while self.running:
            timestamp = int(time.time())
            output_file = os.path.join(log_dir, f"log_{timestamp}.txt")
            logging.info(f"Запуск программы {self.prog_name}, лог в {output_file}")
            process = Popen([sys.executable, self.prog_name],
                            stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()
            with open(output_file, 'w', encoding='utf-8') as f_out:
                f_out.write(stdout.decode('utf-8') + "\n" +
                            stderr.decode('utf-8'))
            self.state.setdefault(self.prog_name, []).append(output_file)
            time.sleep(self.interval)

    def stop(self):
        """Останавливает цикл запуска программы."""
        self.running = False


class FileManagerServer:
    """
    Класс серверного приложения для управления программами.

    Поддерживаемые команды:
      - add <имя_программы>
      - start <имя_программы>
      - stop <имя_программы>
      - delete <имя_программы>
      - getlog <имя_программы>
    """

    def __init__(self, host='0.0.0.0', port=54321, state_file='state.json',
                 interval=10):
        """
        Инициализация сервера.

        Аргументы:
            host (str): Адрес для прослушивания.
            port (int): Порт сервера.
            state_file (str): Файл для хранения состояния.
            interval (int): Интервал запуска программ.
        """
        self.host = host
        self.port = port
        self.state_file = state_file
        self.interval = interval
        self.state = {}
        self.server_socket = None
        self.running = True
        # Хранение запущенных программ: {prog_name: runner}
        self.program_runners = {}

        # Перехват SIGINT для корректного завершения (Ctrl+C)
        signal.signal(signal.SIGINT, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        """
        Обработчик сигнала завершения (Ctrl+C).

        Аргументы:
            signum (int): Номер сигнала.
            frame: Текущий стек вызовов.
        """
        logging.info("Получен сигнал завершения, выключение сервера...")
        self.running = False
        self.shutdown()

    def load_state(self):
        """Загружает состояние из файла state_file."""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r', encoding='utf-8') as f:
                self.state = json.load(f)
                logging.info("Состояние загружено")
        else:
            self.state = {}

    def save_state(self):
        """Сохраняет состояние в файл state_file."""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=4, ensure_ascii=False)
            logging.info("Состояние сохранено")

    def start_program(self, prog_name):
        """
        Создает (если отсутствует) и запускает программу.

        Если файла программы нет, создаётся минимальный Python-файл, который
        выводит дату и время запуска.

        Аргументы:
            prog_name (str): Имя программы (файла).

        Возвращает:
            bool: True, если программа запущена, False если уже запущена.
        """
        if not os.path.exists(prog_name):
            with open(prog_name, 'w', encoding='utf-8') as f:
                f.write(f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
if __name__ == '__main__':
    from datetime import datetime
    print("Программа {prog_name} запущена " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
""")
            os.chmod(prog_name, 0o755)
            logging.info(f"Программа {prog_name} создана как пустой Python-файл")
        elif not os.access(prog_name, os.X_OK):
            os.chmod(prog_name, 0o755)
            logging.info(f"Права на исполнение для {prog_name} изменены")

        if prog_name not in self.program_runners:
            runner = ProgramRunner(prog_name, self.interval, self.state)
            runner.start()
            self.program_runners[prog_name] = runner
            logging.info(f"Программа {prog_name} запущена")
            return True
        else:
            logging.info(f"Программа {prog_name} уже запущена")
            return False

    def stop_program(self, prog_name):
        """
        Останавливает запущенную программу.

        Аргументы:
            prog_name (str): Имя программы.

        Возвращает:
            bool: True, если программа остановлена, False если не запущена.
        """
        if prog_name in self.program_runners:
            runner = self.program_runners.pop(prog_name)
            runner.stop()
            logging.info(f"Программа {prog_name} остановлена")
            return True
        else:
            logging.info(f"Программа {prog_name} не запущена")
            return False

    def delete_program(self, prog_name):
        """
        Останавливает и удаляет программу, а также удаляет её логи.

        Аргументы:
            prog_name (str): Имя программы.

        Возвращает:
            bool: True, если программа успешно удалена, False при ошибке.
        """
        self.stop_program(prog_name)
        if os.path.exists(prog_name):
            try:
                os.remove(prog_name)
                logging.info(f"Файл программы {prog_name} удалён")
            except Exception as e:
                logging.error(f"Ошибка при удалении файла {prog_name}: {e}")
                return False
        log_dir = f"{prog_name}_logs"
        if os.path.exists(log_dir) and os.path.isdir(log_dir):
            try:
                shutil.rmtree(log_dir)
                logging.info(f"Папка логов {log_dir} удалена")
            except Exception as e:
                logging.error(f"Ошибка при удалении папки {log_dir}: {e}")
                return False
        if prog_name in self.state:
            del self.state[prog_name]
        return True

    def client_handler(self, conn, addr):
        """
        Обрабатывает команды, получаемые от клиента.

        Аргументы:
            conn: Сокет соединения с клиентом.
            addr: Адрес клиента.
        """
        logging.info(f"Новое подключение от {addr}")
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                command = data.decode('utf-8').strip()
                if command.startswith("add "):
                    prog_name = command.split(" ", 1)[1]
                    result = self.start_program(prog_name)
                    if result:
                        conn.send(f"Программа {prog_name} добавлена\n"
                                  .encode('utf-8'))
                    else:
                        conn.send(f"Программа {prog_name} уже существует\n"
                                  .encode('utf-8'))
                elif command.startswith("start "):
                    prog_name = command.split(" ", 1)[1]
                    if prog_name in self.program_runners:
                        conn.send(f"Программа {prog_name} уже запущена\n"
                                  .encode('utf-8'))
                    else:
                        if os.path.exists(prog_name):
                            result = self.start_program(prog_name)
                            if result:
                                conn.send(f"Программа {prog_name} запущена\n"
                                          .encode('utf-8'))
                            else:
                                conn.send(f"Ошибка при запуске программы {prog_name}\n"
                                          .encode('utf-8'))
                        else:
                            conn.send(f"Файл программы {prog_name} не найден\n"
                                      .encode('utf-8'))
                elif command.startswith("getlog "):
                    prog_name = command.split(" ", 1)[1]
                    if prog_name in self.state:
                        combined_output = ""
                        for log_file in self.state[prog_name]:
                            if os.path.exists(log_file):
                                with open(log_file, 'r', encoding='utf-8') as lf:
                                    combined_output += lf.read() + "\n"
                        conn.send(combined_output.encode('utf-8'))
                    else:
                        conn.send(f"Программа {prog_name} не найдена\n"
                                  .encode('utf-8'))
                elif command.startswith("stop "):
                    prog_name = command.split(" ", 1)[1]
                    if self.stop_program(prog_name):
                        conn.send(f"Программа {prog_name} остановлена\n"
                                  .encode('utf-8'))
                    else:
                        conn.send(f"Программа {prog_name} не запущена\n"
                                  .encode('utf-8'))
                elif command.startswith("delete "):
                    prog_name = command.split(" ", 1)[1]
                    if self.delete_program(prog_name):
                        conn.send(f"Программа {prog_name} удалена\n"
                                  .encode('utf-8'))
                    else:
                        conn.send(f"Ошибка при удалении программы {prog_name}\n"
                                  .encode('utf-8'))
                else:
                    conn.send("Неизвестная команда\n".encode('utf-8'))
        finally:
            conn.close()

    def run_server(self):
        """Запускает сервер и начинает принимать подключения от клиентов."""
        self.load_state()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.server_socket.settimeout(1.0)
        logging.info(f"Сервер запущен на {self.host}:{self.port}")
        try:
            while self.running:
                try:
                    conn, addr = self.server_socket.accept()
                except socket.timeout:
                    continue
                if not self.running:
                    break
                client_thread = threading.Thread(target=self.client_handler,
                                                 args=(conn, addr),
                                                 daemon=True)
                client_thread.start()
        except Exception as e:
            logging.error(f"Ошибка сервера: {e}")
        finally:
            self.shutdown()

    def shutdown(self):
        """Останавливает сервер, завершает все программы и сохраняет состояние."""
        self.running = False
        for prog in list(self.program_runners.keys()):
            self.stop_program(prog)
        self.save_state()
        if self.server_socket:
            self.server_socket.close()
        logging.info("Сервер завершил работу")


def main():
    """Парсит аргументы командной строки и запускает сервер."""
    parser = argparse.ArgumentParser(description="File Manager Server")
    parser.add_argument('--port', type=int, default=54321,
                        help="Порт сервера (по умолчанию: 54321)")
    parser.add_argument('--interval', type=int, default=10,
                        help="Интервал запуска программ (по умолчанию: 10 сек)")
    args = parser.parse_args()
    server = FileManagerServer(port=args.port, interval=args.interval)
    server.run_server()


if __name__ == '__main__':
    main()
ы