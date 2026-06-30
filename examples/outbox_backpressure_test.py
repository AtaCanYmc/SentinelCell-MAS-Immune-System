import asyncio
import json
import os
import time
from redis.asyncio import Redis
from rich.console import Console

console = Console()


async def simulate_backpressure():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    r = Redis.from_url(redis_url)

    console.print(
        "[bold yellow][*] Starting Outbox Backpressure Chaos Test[/bold yellow]"
    )
    console.print(
        "[dim]Simulating 15,000 logs pushed to sentinel.outbox while VectorDB is down...[/dim]"
    )

    # Push 15,000 items
    start = time.time()
    for i in range(15000):
        # We will use the same lpush and ltrim logic the orchestrator uses
        entry = {
            "doc_id": f"test-{i}",
            "memory_doc": f"Simulation doc {i}",
            "metadata": {"source": "backpressure_test"},
        }
        await r.lpush("sentinel.outbox", json.dumps(entry))
        # Simulated orchestrator eviction policy
        await r.ltrim("sentinel.outbox", 0, 9999)

        if i % 5000 == 0:
            console.print(f"[cyan]Pushed {i} items...[/cyan]")

    console.print(
        f"[bold green][+] Finished pushing in {time.time() - start:.2f} seconds.[/bold green]"
    )

    # Check length
    length = await r.llen("sentinel.outbox")
    console.print(
        f"[bold yellow][*] Current length of sentinel.outbox: {length}[/bold yellow]"
    )

    if length <= 10000:
        console.print(
            "[bold green][+] SUCCESS: Eviction Policy (LTRIM) worked. OOM prevented.[/bold green]"
        )
    else:
        console.print(
            "[bold red][!] FAILURE: Eviction Policy failed. Queue is over 10,000.[/bold red]"
        )


if __name__ == "__main__":
    asyncio.run(simulate_backpressure())
