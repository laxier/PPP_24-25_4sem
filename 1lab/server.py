#!/usr/bin/env python3
"""
File Manager Server

Supported commands from the client:
  - add <program_name>      : Create (if missing) and start a program.
  - start <program_name>    : Start a program if it exists and is not running.
  - stop <program_name>     : Stop a running program.
  - delete <program_name>   : Delete a program and its logs.
  - getlog <program_name>   : Retrieve logs for the specified program.
  - programs                : List all known programs with their status.
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

# Server logging configuration
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class ProgramRunner(threading.Thread):
    """
    Thread that repeatedly runs a program and saves its output logs.

    Attributes:
        prog_name (str): Name of the program file.
        interval (int): Delay (in seconds) between runs.
        state (dict): Shared state dict for storing logs and status.
        running (bool): Flag to control the running loop.
    """

    def __init__(self, prog_name, interval, state):
        super().__init__(daemon=True)
        self.prog_name = prog_name
        self.interval = interval
        self.state = state
        self.running = True

    def run(self):
        """
        Executes the program in a loop and writes the output to log files.
        """
        log_dir = f"{self.prog_name}_logs"
        os.makedirs(log_dir, exist_ok=True)
        while self.running:
            timestamp = int(time.time())
            output_file = os.path.join(log_dir, f"log_{timestamp}.txt")
            logging.info(f"Running program {self.prog_name}, log: {output_file}")
            process = Popen([sys.executable, self.prog_name],
                            stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()
            with open(output_file, 'w', encoding='utf-8') as f_out:
                f_out.write(stdout.decode('utf-8') + "\n" +
                            stderr.decode('utf-8'))
            self.state.setdefault(self.prog_name, {})\
                      .setdefault("logs", []).append(output_file)
            time.sleep(self.interval)

    def stop(self):
        """
        Stops the running loop.
        """
        self.running = False


class FileManagerServer:
    """
    Server application for managing programs.

    Supported commands:
      - add <program_name>
      - start <program_name>
      - stop <program_name>
      - delete <program_name>
      - getlog <program_name>
      - programs
    """

    def __init__(self, host='0.0.0.0', port=54321, state_file='state.json',
                 interval=10):
        """
        Initialize the server.

        Args:
            host (str): Host address to bind.
            port (int): Port number.
            state_file (str): JSON file for saving the state.
            interval (int): Program run interval in seconds.
        """
        self.host = host
        self.port = port
        self.state_file = state_file
        self.interval = interval
        self.state = {}  # Expected format: { prog_name: {"logs": [...], "status": "running"/"stopped"} }
        self.server_socket = None
        self.running = True
        self.program_runners = {}  # Mapping of running programs: { prog_name: runner }

        signal.signal(signal.SIGINT, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        """
        Signal handler for graceful shutdown.
        """
        logging.info("Shutdown signal received, shutting down server...")
        self.running = False
        self.shutdown()

    def load_state(self):
        """
        Loads the JSON state from state_file.
        """
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r', encoding='utf-8') as f:
                self.state = json.load(f)
                logging.info("State loaded")
        else:
            self.state = {}

    def save_state(self):
        """
        Saves the current state to state_file.
        """
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=4, ensure_ascii=False)
            logging.info("State saved")

    def start_program(self, prog_name):
        """
        Creates (if missing) and starts the program.
        
        If the program file does not exist, it creates a minimal Python file that
        prints its start time. Updates the state with a "status" field.

        Args:
            prog_name (str): Name of the program file.

        Returns:
            bool: True if started, False if already running.
        """
        if not os.path.exists(prog_name):
            with open(prog_name, 'w', encoding='utf-8') as f:
                f.write(f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if __name__ == '__main__':
    from datetime import datetime
    print("Программа {prog_name} запущена " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
""")
            os.chmod(prog_name, 0o755)
            logging.info(f"Program {prog_name} created as a minimal Python file")
            self.state.setdefault(prog_name, {})["logs"] = []
            self.state[prog_name]["status"] = "stopped"
        elif not os.access(prog_name, os.X_OK):
            os.chmod(prog_name, 0o755)
            logging.info(f"Execution permissions updated for {prog_name}")

        if prog_name not in self.program_runners:
            runner = ProgramRunner(prog_name, self.interval, self.state)
            runner.start()
            self.program_runners[prog_name] = runner
            # Update status in state
            self.state.setdefault(prog_name, {})["status"] = "running"
            logging.info(f"Program {prog_name} started")
            return True
        else:
            logging.info(f"Program {prog_name} is already running")
            return False

    def stop_program(self, prog_name):
        """
        Stops a running program.

        Args:
            prog_name (str): Name of the program.

        Returns:
            bool: True if stopped, False if not running.
        """
        if prog_name in self.program_runners:
            runner = self.program_runners.pop(prog_name)
            runner.stop()
            self.state.setdefault(prog_name, {})["status"] = "stopped"
            logging.info(f"Program {prog_name} stopped")
            return True
        else:
            logging.info(f"Program {prog_name} is not running")
            return False

    def delete_program(self, prog_name):
        """
        Stops and deletes a program along with its logs.

        Args:
            prog_name (str): Name of the program.

        Returns:
            bool: True if deleted successfully, False on error.
        """
        self.stop_program(prog_name)
        if os.path.exists(prog_name):
            try:
                os.remove(prog_name)
                logging.info(f"Program file {prog_name} deleted")
            except Exception as e:
                logging.error(f"Error deleting file {prog_name}: {e}")
                return False
        log_dir = f"{prog_name}_logs"
        if os.path.exists(log_dir) and os.path.isdir(log_dir):
            try:
                shutil.rmtree(log_dir)
                logging.info(f"Log directory {log_dir} deleted")
            except Exception as e:
                logging.error(f"Error deleting directory {log_dir}: {e}")
                return False
        if prog_name in self.state:
            del self.state[prog_name]
        return True

    def get_programs_status(self):
        """
        Retrieves the status of all known programs.

        Returns:
            str: A formatted string listing each program and its status.
        """
        # Union of programs from state and currently running ones
        all_programs = set(self.state.keys()).union(set(self.program_runners.keys()))
        if not all_programs:
            return "No known programs.\n"
        output = ""
        for prog in sorted(all_programs):
            status = self.state.get(prog, {}).get("status", "stopped")
            output += f"{prog}: {status}\n"
        return output

    def client_handler(self, conn, addr):
        """
        Handles client commands.

        Args:
            conn: Client connection socket.
            addr: Client address.
        """
        logging.info(f"New connection from {addr}")
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
                        conn.send(f"Program {prog_name} added and started\n".encode('utf-8'))
                    else:
                        conn.send(f"Program {prog_name} already exists\n".encode('utf-8'))
                elif command.startswith("start "):
                    prog_name = command.split(" ", 1)[1]
                    if prog_name in self.program_runners:
                        conn.send(f"Program {prog_name} is already running\n".encode('utf-8'))
                    else:
                        if os.path.exists(prog_name):
                            result = self.start_program(prog_name)
                            if result:
                                conn.send(f"Program {prog_name} started\n".encode('utf-8'))
                            else:
                                conn.send(f"Error starting program {prog_name}\n".encode('utf-8'))
                        else:
                            conn.send(f"Program file {prog_name} not found\n".encode('utf-8'))
                elif command.startswith("getlog "):
                    prog_name = command.split(" ", 1)[1]
                    if prog_name in self.state and "logs" in self.state[prog_name]:
                        combined_output = ""
                        for log_file in self.state[prog_name]["logs"]:
                            if os.path.exists(log_file):
                                with open(log_file, 'r', encoding='utf-8') as lf:
                                    combined_output += lf.read() + "\n"
                        conn.send(combined_output.encode('utf-8'))
                    else:
                        conn.send(f"Program {prog_name} not found\n".encode('utf-8'))
                elif command.startswith("stop "):
                    prog_name = command.split(" ", 1)[1]
                    if self.stop_program(prog_name):
                        conn.send(f"Program {prog_name} stopped\n".encode('utf-8'))
                    else:
                        conn.send(f"Program {prog_name} is not running\n".encode('utf-8'))
                elif command.startswith("delete "):
                    prog_name = command.split(" ", 1)[1]
                    if self.delete_program(prog_name):
                        conn.send(f"Program {prog_name} deleted\n".encode('utf-8'))
                    else:
                        conn.send(f"Error deleting program {prog_name}\n".encode('utf-8'))
                elif command == "programs":
                    status_output = self.get_programs_status()
                    conn.send(status_output.encode('utf-8'))
                else:
                    conn.send("Unknown command\n".encode('utf-8'))
        finally:
            conn.close()

    def run_server(self):
        """
        Starts the server and begins accepting client connections.
        """
        self.load_state()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.server_socket.settimeout(1.0)
        logging.info(f"Server running on {self.host}:{self.port}")
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
            logging.error(f"Server error: {e}")
        finally:
            self.shutdown()

    def shutdown(self):
        """
        Stops the server, stops all running programs, and saves state.
        """
        self.running = False
        for prog in list(self.program_runners.keys()):
            self.stop_program(prog)
        self.save_state()
        if self.server_socket:
            self.server_socket.close()
        logging.info("Server shut down")


def main():
    """
    Parses command-line arguments and starts the server.
    """
    parser = argparse.ArgumentParser(description="File Manager Server")
    parser.add_argument('--port', type=int, default=54321,
                        help="Server port (default: 54321)")
    parser.add_argument('--interval', type=int, default=10,
                        help="Interval between program runs (default: 10 sec)")
    args = parser.parse_args()
    server = FileManagerServer(port=args.port, interval=args.interval)
    server.run_server()


if __name__ == '__main__':
    main()
