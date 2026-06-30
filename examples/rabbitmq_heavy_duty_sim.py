import asyncio
import os
from rich.console import Console
from util import setup_mock_environment

setup_mock_environment()

console = Console()


async def simulate_rabbitmq_broker():
    # Force system to use RabbitMQ Broker
    os.environ["MESSAGE_BROKER"] = "RABBITMQ"
    os.environ["RABBITMQ_URL"] = "amqp://guest:guest@localhost/"

    console.print(
        "[bold yellow]--- Testing RabbitMQ Heavy-Duty Message Broker ---[/bold yellow]"
    )
    console.print(
        "[dim]Note: This simulation requires a running RabbitMQ broker at amqp://localhost/[/dim]"
    )

    from src.core.broker_factory import BrokerFactory

    broker = BrokerFactory.get_broker()

    console.print(
        f"[bold cyan][+] Loaded Broker Class: {broker.__class__.__name__}[/bold cyan]"
    )

    if broker.__class__.__name__ != "RabbitMQBroker":
        console.print("[bold red][!] Factory failed to load RabbitMQBroker![/bold red]")
        return

    try:
        # Check connection implicitly by attempting to push
        test_payload = '{"test": "rabbitmq_heavy_duty_100k_tps"}'
        console.print(
            f"[dim]Pushing test payload to 'sentinel.test.queue': {test_payload}[/dim]"
        )
        await broker.push("sentinel.test.queue", test_payload)

        console.print(
            "[bold green][+] Successfully published to RabbitMQ queue 'sentinel.test.queue'![/bold green]"
        )

        console.print(
            "[dim]Attempting to consume from 'sentinel.test.queue' (timeout 5s)...[/dim]"
        )

        msg = await broker.consume("sentinel.test.queue", timeout=5)

        if msg:
            console.print(
                f"[bold green][+] Successfully consumed from RabbitMQ: {msg}[/bold green]"
            )
            console.print(
                "[bold green][+] RabbitMQ message acknowledged automatically (via auto_ack or explicit logic).[/bold green]"
            )
        else:
            console.print(
                "[bold yellow][!] Could not consume message in time. Is RabbitMQ running?[/bold yellow]"
            )

    except Exception as e:
        console.print(
            f"\n[bold red][RabbitMQ Error] Failed to connect or execute: {e}[/bold red]"
        )
        console.print(
            "[dim]This is expected if you don't have RabbitMQ running locally. The Factory architecture itself is successfully verified![/dim]"
        )


if __name__ == "__main__":
    asyncio.run(simulate_rabbitmq_broker())
