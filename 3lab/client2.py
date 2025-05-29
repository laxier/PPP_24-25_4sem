import argparse
from celery.result import AsyncResult
from app.celery.tasks import bruteforce_task
from app.core.celery_app import celery

def send_task(args):
    result = bruteforce_task.delay(
        args.user_id,
        args.target_hash,
        args.charset,
        args.max_length,
        args.hash_type
    )
    print(f"🎯 Task sent! Task ID: {result.id}")

def check_status(args):
    result = AsyncResult(args.task_id, app=celery)
    print(f"📦 Task status: {result.status}")
    if result.ready():
        print(f"✅ Result: {result.result}")

def main():
    parser = argparse.ArgumentParser(description="Bruteforce client for Celery")

    subparsers = parser.add_subparsers(dest="command")

    # Subcommand: send
    send_parser = subparsers.add_parser("send", help="Send a bruteforce task")
    send_parser.add_argument("--user_id", type=int, default=0)
    send_parser.add_argument("--target_hash", type=str, required=True)
    send_parser.add_argument("--charset", type=str, default="abcdefghijklmnopqrstuvwxyz0123456789")
    send_parser.add_argument("--max_length", type=int, default=8)
    send_parser.add_argument("--hash_type", type=str, default="md5")

    # Subcommand: status
    status_parser = subparsers.add_parser("status", help="Check task status")
    status_parser.add_argument("--task_id", type=str, required=True)

    args = parser.parse_args()

    if args.command == "send":
        send_task(args)
    elif args.command == "status":
        check_status(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
