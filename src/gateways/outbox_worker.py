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

    while True:
        try:
            # Pop from outbox (blocking with timeout)
            result = await r.brpop("sentinel.outbox", timeout=5)
            if result:
                _, message = result
                entry = json.loads(message)

                # Write to VectorDB
                memory_store.add_memory(
                    doc_id=entry["doc_id"],
                    memory_doc=entry["memory_doc"],
                    metadata=entry["metadata"],
                )
                console.print(
                    f"[dim green]Outbox -> Synced doc {entry['doc_id']} to VectorDB[/dim green]"
                )
        except Exception as e:
            console.print(f"[bold red]Outbox Worker Error: {e}[/bold red]")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(process_outbox())
