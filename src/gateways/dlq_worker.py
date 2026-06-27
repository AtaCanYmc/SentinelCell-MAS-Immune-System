import orjson
import asyncio
from src.core.broker_factory import BrokerFactory
from src.core.tracer import get_tracer, extract_trace_context, inject_trace_context
from rich.console import Console

console = Console()
tracer = get_tracer()


async def process_dlq():
    broker = BrokerFactory.get_broker()

    dlq_queue = "sentinel.dlq"
    processing_queue = "sentinel.dlq.processing"
    main_bus = "sentinel.in"

    while True:
        try:
            # 1. ATOMIC POP: Move item from DLQ to processing queue safely
            raw_entry, ack_token = await broker.pop_atomic(
                dlq_queue, processing_queue, timeout=5
            )

            if not raw_entry:
                continue  # Timeout reached, no messages

            try:
                entry = orjson.loads(raw_entry)

                # 2. DECIDE: Drop or Retry
                ctx = extract_trace_context(entry)
                with tracer.start_as_current_span("DLQ.Process", context=ctx) as span:
                    if "dlq_retry_count" not in entry:
                        entry["dlq_retry_count"] = 0

                    entry["dlq_retry_count"] += 1
                    span.set_attribute("dlq.retry_count", entry["dlq_retry_count"])

                    if entry["dlq_retry_count"] > 3:
                        console.print(
                            f"[dim red]Dropping poisoned payload {entry.get('source')} -> {entry.get('target')} (Max Retries)[/dim red]"
                        )
                        span.set_attribute("dlq.dropped", True)
                    else:
                        # 3. RETRY: Push to the main bus
                        inject_trace_context(entry)
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
                            f"[dim green]Re-queued payload {entry.get('source')} -> {entry.get('target')}[/dim green]"
                        )

                    # 4. COMMIT: Remove from processing queue ONLY after we've successfully handled it
                    await broker.acknowledge(processing_queue, ack_token)

            except Exception as e:
                console.print(
                    f"[bold red][Atomic DLQ] Failed to parse payload: {e}[/bold red]"
                )
                # We could leave it in the processing queue or move it to a 'poison' queue.
                # For now, remove it to prevent endless loops on totally broken data.
                await broker.acknowledge(processing_queue, ack_token)

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
