import json
import asyncio
from src.core.broker_factory import BrokerFactory
from src.core.tracer import get_tracer, extract_trace_context
from rich.console import Console

console = Console()
tracer = get_tracer()


async def process_outbox():
    broker = BrokerFactory.get_broker()

    # Import Memory Factory for VectorDB
    from src.core.memory_factory import MemoryFactory

    memory_store = MemoryFactory.get_memory_store()

    console.print(
        "[bold cyan][*] Outbox Worker Started. Listening to sentinel.outbox...[/bold cyan]"
    )

    # Startup Recovery: move stuck items back to the main outbox
    while True:
        # Startup Recovery for Redis, not strictly needed for Kafka offset-based but safe
        try:
            stuck_item = await broker.pop_atomic(
                "sentinel.outbox_processing", "sentinel.outbox", timeout=1
            )
            if not stuck_item:
                break
        except Exception:
            break
        console.print(
            "[dim yellow][!] Recovered stuck item from processing queue.[/dim yellow]"
        )

    while True:
        try:
            # Pop from outbox to processing (blocking with timeout)
            # Reliable Queue Pattern (At-least-once delivery)
            message = await broker.pop_atomic(
                "sentinel.outbox", "sentinel.outbox_processing", timeout=5
            )
            if message:
                entry = json.loads(message)

                ctx = extract_trace_context(entry)
                with tracer.start_as_current_span("Outbox.Sync", context=ctx) as span:
                    span.set_attribute("outbox.doc_id", entry.get("doc_id", "Unknown"))

                    # Write to VectorDB
                    memory_store.add_memory(
                        doc_id=entry["doc_id"],
                        memory_doc=entry["memory_doc"],
                        metadata=entry["metadata"],
                    )

                    # Acknowledge: remove from processing queue
                    await broker.acknowledge("sentinel.outbox_processing", message)

                console.print(
                    f"[dim green]Outbox -> Synced doc {entry['doc_id']} to VectorDB[/dim green]"
                )
        except Exception as e:
            console.print(f"[bold red]Outbox Worker Error: {e}[/bold red]")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(process_outbox())
