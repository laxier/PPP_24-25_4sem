#!/usr/bin/env python3
"""
File Manager Client

Connects to the server and sends commands:
  - add <program_name>      : Create and start a program.
  - start <program_name>    : Start an existing program.
  - stop <program_name>     : Stop a running program.
  - delete <program_name>   : Delete a program and its logs.
  - getlog <program_name>   : Get logs for a program.
  - programs                : List all programs with their status.
  - exit                    : Exit the client.
"""

import socket
import argparse

def main():
    """
    Parses command-line arguments, connects to the server,
    and allows the user to send commands.
    """
    parser = argparse.ArgumentParser(description="File Manager Client")
    parser.add_argument('--host', type=str, default='127.0.0.1',
                        help="Server IP (default: 127.0.0.1)")
    parser.add_argument('--port', type=int, default=54321,
                        help="Server port (default: 54321)")
    args = parser.parse_args()

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((args.host, args.port))
        print(f"Connected to server {args.host}:{args.port}")
    except Exception as e:
        print(f"Failed to connect to server: {e}")
        return

    print("Available commands:")
    print("  add <program_name>    - Create and start a program")
    print("  start <program_name>  - Start a program if not running")
    print("  stop <program_name>   - Stop a running program")
    print("  delete <program_name> - Delete a program and its logs")
    print("  getlog <program_name> - Get logs for the program")
    print("  programs              - List all programs and their status")
    print("  exit                  - Exit the client")

    try:
        while True:
            command = input("Enter command: ").strip()
            if not command:
                continue
            if command.lower() == "exit":
                print("Exiting client.")
                break
            try:
                client_socket.send(command.encode('utf-8'))
                full_response = b""
                while True:
                    part = client_socket.recv(4096)
                    if len(part) == 0:
                        print("Server closed the connection.")
                        return
                    full_response += part
                    if b"END_OF_RESPONSE" in full_response:
                        break

                print("Server response:")
                print(full_response.decode('utf-8'))
            except Exception as e:
                print(f"Error sending command: {e}")
                break
    finally:
        client_socket.close()

if __name__ == '__main__':
    main()


if __name__ == '__main__':
    main()
