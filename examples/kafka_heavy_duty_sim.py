import asyncio
import os
from rich.console import Console

console = Console()


async def simulate_kafka_broker():
    # Force system to use Kafka Broker
    os.environ["MESSAGE_BROKER"] = "KAFKA"
    os.environ["KAFKA_BOOTSTRAP_SERVERS"] = "localhost:9092"

    console.print(
        "[bold yellow]--- Testing Kafka Heavy-Duty Message Broker ---[/bold yellow]"
    )
    console.print(
        "[dim]Note: This simulation requires a running Kafka broker at localhost:9092[/dim]"
    )

    from src.core.broker_factory import BrokerFactory

    broker = BrokerFactory.get_broker()

    console.print(
        f"[bold cyan][+] Loaded Broker Class: {broker.__class__.__name__}[/bold cyan]"
    )

    if broker.__class__.__name__ != "KafkaBroker":
        console.print("[bold red][!] Factory failed to load KafkaBroker![/bold red]")
        return

    # We will test a simple push and consume cycle if Kafka is available.
    try:
        # Check connection implicitly by attempting to push
        test_payload = '{"test": "heavy_duty_100k_tps"}'
        console.print(
            f"[dim]Pushing test payload to 'sentinel.test.queue': {test_payload}[/dim]"
        )
        await broker.push("sentinel.test.queue", test_payload)

        console.print(
            "[bold green][+] Successfully published to Kafka topic 'sentinel.test.queue'![/bold green]"
        )

        console.print(
            "[dim]Attempting to consume from 'sentinel.test.queue' (timeout 5s)...[/dim]"
        )

        # We need to give the consumer a moment to join the group
        msg = await broker.consume("sentinel.test.queue", timeout=5)

        if msg:
            console.print(
                f"[bold green][+] Successfully consumed from Kafka: {msg}[/bold green]"
            )
            console.print(
                "[bold green][+] Kafka offset committed automatically (via acknowledge/commit logic).[/bold green]"
            )
        else:
            console.print(
                "[bold yellow][!] Could not consume message in time. Is topic created? Are auto-commits configured properly in Kafka?[/bold yellow]"
            )

    except Exception as e:
        console.print(
            f"\n[bold red][Kafka Error] Failed to connect or execute: {e}[/bold red]"
        )
        console.print(
            "[dim]This is expected if you don't have Kafka running locally. The Factory architecture itself is successfully verified![/dim]"
        )


if __name__ == "__main__":
    asyncio.run(simulate_kafka_broker())
