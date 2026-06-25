import json
import asyncio
from src.core.broker_factory import BrokerFactory
from src.agents.validator_agent import SentinelCell
from rich.console import Console

console = Console()


async def mq_worker():
    broker = BrokerFactory.get_broker()
    sentinel = SentinelCell()

    console.print("[bold cyan]SentinelCell Ingress MQ Worker started...[/bold cyan]")

    while True:
        try:
            # broker.consume blocks until a message is available
            data_str = await broker.consume("sentinel.in", timeout=0)
            if data_str:
                # We expect the payload to be wrapped with source and target info for routing
                # Example: {"source": "AgentA", "target": "AgentB", "payload": "{\"status\":\"ok\"}"}
                try:
                    envelope = json.loads(data_str)
                    source = envelope.get("source", "Unknown")
                    target = envelope.get("target", "Unknown")
                    payload = envelope.get("payload", data_str)

                    if isinstance(payload, dict):
                        payload = json.dumps(payload)

                    result = await sentinel.intercept(
                        source=source, target=target, payload=payload
                    )

                    if result:
                        # Push the valid/healed message to 'sentinel.out'
                        await broker.push("sentinel.out", json.dumps(result))
                        console.print(
                            "[green]Message processed and forwarded to sentinel.out[/green]"
                        )
                    else:
                        console.print("[red]Message rejected and dropped.[/red]")

                except json.JSONDecodeError:
                    console.print(
                        "[red]Invalid envelope format. Dropping message.[/red]"
                    )

        except Exception as e:
            console.print(f"[bold red]Worker Error: {e}[/bold red]")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(mq_worker())
