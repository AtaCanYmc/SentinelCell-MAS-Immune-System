import json
import os
import sys
import redis
from rich.console import Console

console = Console()


def replay_dlq():
    dlq_path = os.path.join(os.getcwd(), ".antigravity", "logs", "dlq.json")
    if not os.path.exists(dlq_path):
        console.print("[bold red]No DLQ file found![/bold red]")
        sys.exit(1)

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    r = redis.Redis.from_url(redis_url)

    replayed = 0
    with open(dlq_path, "r") as f:
        lines = f.readlines()

    with open(dlq_path, "w") as f:
        for line in lines:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                # Ensure it's pushed back exactly as it came from the source
                payload_to_push = entry.get("payload")

                # Check if it was poisoned or oversized
                reason = entry.get("reason", "")
                if (
                    "Too Large" in reason
                    or "Poisoning" in reason
                    or "SECURITY" in reason.upper()
                ):
                    console.print(
                        f"[bold yellow]Skipping malicious/oversized payload:[/bold yellow] {reason}"
                    )
                    # Write it back to DLQ since we skip it
                    f.write(line)
                    continue

                r.lpush(
                    "sentinel.in",
                    json.dumps(
                        {
                            "source": entry.get("source"),
                            "target": entry.get("target"),
                            "payload": payload_to_push,
                        }
                    ),
                )
                replayed += 1
                console.print(
                    f"[bold green]Replayed message from {entry.get('source')} to {entry.get('target')}[/bold green]"
                )
            except Exception as e:
                console.print(f"[bold red]Failed to replay:[/bold red] {e}")
                f.write(line)

    console.print(f"[bold cyan]Total replayed messages: {replayed}[/bold cyan]")


if __name__ == "__main__":
    replay_dlq()
