import orjson
import os
import asyncio
import redis.asyncio as redis
from rich.console import Console

console = Console()
DLQ_PATH = os.path.join(os.getcwd(), ".antigravity", "logs", "dlq.json")


async def process_dlq():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    r = redis.from_url(redis_url)

    while True:
        if not os.path.exists(DLQ_PATH):
            await asyncio.sleep(10)
            continue

        try:
            with open(DLQ_PATH, "r") as f:
                lines = f.readlines()

            retained_lines = []
            replayed_count = 0

            for line in lines:
                if not line.strip():
                    continue
                try:
                    entry = orjson.loads(line)
                    reason = entry.get("reason", "")

                    # Drop malicious or oversized immediately
                    if (
                        "Too Large" in reason
                        or "Poisoning" in reason
                        or "SECURITY" in reason.upper()
                    ):
                        console.print(
                            "[bold yellow][DLQ Worker] Permanently dropping malicious/oversized payload.[/bold yellow]"
                        )
                        continue

                    # For a real exponential backoff, we'd track IDs and retries.
                    # Here we simulate an automated retry of valid-but-failed payloads.
                    await r.lpush(
                        "sentinel.in",
                        orjson.dumps(
                            {
                                "source": entry.get("source"),
                                "target": entry.get("target"),
                                "payload": entry.get("payload"),
                            }
                        ).decode("utf-8"),
                    )
                    replayed_count += 1
                    console.print(
                        f"[bold green][DLQ Worker] Replayed message from {entry.get('source')} to {entry.get('target')}[/bold green]"
                    )
                except Exception:
                    retained_lines.append(line)

            # Write back retained lines (the ones that failed to parse or weren't replayed)
            with open(DLQ_PATH, "w") as f:
                for line in retained_lines:
                    f.write(line)

            if replayed_count > 0:
                console.print(
                    f"[bold cyan][DLQ Worker] Successfully replayed {replayed_count} messages.[/bold cyan]"
                )

        except Exception as e:
            console.print(f"[bold red][DLQ Worker] Error reading DLQ:[/bold red] {e}")

        # Exponential Backoff/Polling simulation (every 30 seconds for demonstration)
        await asyncio.sleep(30)


if __name__ == "__main__":
    console.print("[bold cyan][*] Automated DLQ Replay Worker Started[/bold cyan]")
    asyncio.run(process_dlq())
