import orjson
import asyncio
from src.core.broker_factory import BrokerFactory
from rich.console import Console

console = Console()


async def process_dlq():
    broker = BrokerFactory.get_broker()

    dlq_queue = "sentinel.dlq"
    processing_queue = "sentinel.dlq.processing"
    main_bus = "sentinel.in"

    while True:
        try:
            # 1. ATOMIC POP: Move item from DLQ to processing queue safely
            raw_entry = await broker.pop_atomic(dlq_queue, processing_queue, timeout=5)

            if not raw_entry:
                continue  # Timeout reached, no messages

            try:
                entry = orjson.loads(raw_entry)
                reason = entry.get("reason", "")

                # 2. DECIDE: Drop or Retry
                if (
                    "Too Large" in reason
                    or "Poisoning" in reason
                    or "SECURITY" in reason.upper()
                ):
                    console.print(
                        f"[bold yellow][Atomic DLQ] Permanently dropping malicious/oversized payload from {entry.get('source')}.[/bold yellow]"
                    )
                else:
                    # 3. RETRY: Push to the main bus
                    await broker.push(
                        main_bus,
                        orjson.dumps(
                            {
                                "source": entry.get("source"),
                                "target": entry.get("target"),
                                "payload": entry.get("payload"),
                            }
                        ).decode("utf-8"),
                    )
                    console.print(
                        f"[bold green][Atomic DLQ] Replayed message from {entry.get('source')} to {entry.get('target')}[/bold green]"
                    )

                # 4. COMMIT: Remove from processing queue ONLY after we've successfully handled it
                await broker.acknowledge(processing_queue, raw_entry)

            except Exception as e:
                console.print(
                    f"[bold red][Atomic DLQ] Failed to parse payload: {e}[/bold red]"
                )
                # We could leave it in the processing queue or move it to a 'poison' queue.
                # For now, remove it to prevent endless loops on totally broken data.
                await broker.acknowledge(processing_queue, raw_entry)

        except Exception as e:
            console.print(
                f"[bold red][Atomic DLQ] Broker Connection Error: {e}[/bold red]"
            )
            await asyncio.sleep(5)


if __name__ == "__main__":
    console.print(
        "[bold cyan][*] True Atomic Redis DLQ Worker Started (BRPOPLPUSH)[/bold cyan]"
    )
    asyncio.run(process_dlq())
