import asyncio
import json
from rich.console import Console
from rich.panel import Panel
from src.agents.validator_agent import SentinelCell

console = Console()


async def mq_guardian_worker(
    in_queue: asyncio.Queue, out_queue: asyncio.Queue, sentinel: SentinelCell
):
    """Simulates the background MQ worker (like src/gateways/redis_mq.py)."""
    console.print(
        "[dim cyan][Guardian Worker] Subscribed to 'sentinel.in' queue...[/dim cyan]\n"
    )
    while True:
        message = await in_queue.get()
        if message == "STOP":
            break

        data_str = message
        try:
            envelope = json.loads(data_str)
            source = envelope.get("source", "Unknown")
            target = envelope.get("target", "Unknown")
            payload = envelope.get("payload", data_str)

            console.print(
                "[bold yellow][SentinelCell] Message intercepted from Queue! Analyzing...[/bold yellow]"
            )

            if isinstance(payload, dict):
                payload = json.dumps(payload)

            result = await sentinel.intercept(
                source=source, target=target, payload=payload
            )

            if result:
                await out_queue.put(json.dumps(result))
                console.print(
                    "\n[bold green][SentinelCell] 💉 Payload Cured! Pushing safe data to 'sentinel.out' queue.[/bold green]\n"
                )
            else:
                console.print(
                    "\n[bold red][SentinelCell] ⛔ Infection unrecoverable. Packet burned.[/bold red]\n"
                )
                await out_queue.put("DROPPED")
        except json.JSONDecodeError:
            pass

        in_queue.task_done()


async def producer(in_queue: asyncio.Queue):
    """Simulates Agent_Alpha blindly pushing corrupted data to the MQ."""
    await asyncio.sleep(1)  # Simulate network delay
    console.print(
        Panel(
            "Agent_Alpha has hallucinatory bugs and is pushing a completely malformed JSON to the messaging queue.\n"
            "It expects Agent_Beta to process it, which would normally crash the entire system.",
            title="[bold red]Agent_Alpha (Producer)[/bold red]",
            border_style="red",
        )
    )

    # Missing required 'status' and 'message' fields, totally broken schema
    sick_payload = json.dumps(
        {
            "source": "Agent_Alpha",
            "target": "Agent_Beta",
            "payload": '{"unexpected_field": "system_panic", "broken": true}',
        }
    )
    console.print(f"[dim red]>> Pushing to sentinel.in:[/dim red] {sick_payload}\n")

    await in_queue.put(sick_payload)


async def consumer(out_queue: asyncio.Queue):
    """Simulates Agent_Beta consuming clean data from the MQ."""
    console.print(
        "[dim magenta][Agent_Beta (Consumer)] Blocked, waiting for safe data on 'sentinel.out'...[/dim magenta]"
    )
    clean_data = await out_queue.get()

    console.print(
        Panel.fit(
            f"{clean_data}",
            title="[bold green]Agent_Beta (Consumer) Received Data[/bold green]",
            border_style="green",
        )
    )
    out_queue.task_done()


async def main():
    console.print(
        Panel.fit(
            "[bold cyan]🌉 DISTRIBUTED MESSAGE QUEUE (MQ) SIMULATION 🌉[/bold cyan]\n"
            "Simulating a distributed event-driven architecture (e.g. Kafka, RabbitMQ, Redis PubSub).\n"
            "Agents do NOT talk directly. SentinelCell acts as the 'Queue Guardian' (Immune System).",
            border_style="cyan",
        )
    )

    # In-memory queues to simulate Redis/RabbitMQ
    in_queue = asyncio.Queue()
    out_queue = asyncio.Queue()
    sentinel = SentinelCell()
    try:
        # Start the Guardian (Immune System) as a persistent background worker
        guardian_task = asyncio.create_task(
            mq_guardian_worker(in_queue, out_queue, sentinel)
        )

        # Start the Consumer listening on the out-queue
        consumer_task = asyncio.create_task(consumer(out_queue))

        # Start Producer pushing to the in-queue
        await producer(in_queue)

        # Wait for consumer to safely receive and process the healed payload
        await consumer_task

        # Shut down the Guardian
        await in_queue.put("STOP")
        await guardian_task

        console.print(
            "[bold green]✅ MQ Simulation Complete. Downstream consumers were fully protected![/bold green]"
        )
    finally:
        await sentinel.stop()


if __name__ == "__main__":
    asyncio.run(main())
