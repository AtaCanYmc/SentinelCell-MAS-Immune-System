import os
import json
import asyncio
import redis.asyncio as redis
from rich.console import Console

console = Console()


async def process_outbox():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    r = redis.from_url(redis_url)

    # Import Memory Factory for VectorDB
    from src.core.memory_factory import MemoryFactory

    memory_store = MemoryFactory.get_memory_store()

    console.print(
        "[bold cyan][*] Outbox Worker Started. Listening to sentinel.outbox...[/bold cyan]"
    )

    # Startup Recovery: move stuck items back to the main outbox
    while True:
        stuck_item = await r.rpop("sentinel.outbox_processing")
        if not stuck_item:
            break
        await r.lpush("sentinel.outbox", stuck_item)
        console.print(
            "[dim yellow][!] Recovered stuck item from processing queue.[/dim yellow]"
        )

    while True:
        try:
            # Pop from outbox to processing (blocking with timeout)
            # Reliable Queue Pattern (At-least-once delivery)
            message = await r.brpoplpush(
                "sentinel.outbox", "sentinel.outbox_processing", timeout=5
            )
            if message:
                entry = json.loads(message)

                # Write to VectorDB
                memory_store.add_memory(
                    doc_id=entry["doc_id"],
                    memory_doc=entry["memory_doc"],
                    metadata=entry["metadata"],
                )

                # Acknowledge: remove from processing queue
                await r.lrem("sentinel.outbox_processing", 1, message)

                console.print(
                    f"[dim green]Outbox -> Synced doc {entry['doc_id']} to VectorDB[/dim green]"
                )
        except Exception as e:
            console.print(f"[bold red]Outbox Worker Error: {e}[/bold red]")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(process_outbox())
