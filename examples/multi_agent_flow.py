import asyncio
import json
from rich.console import Console
from src.agents.validator_agent import SentinelCell

console = Console()


class ProducerAgent:
    def emit_data(self):
        # Emitting malformed data intentionally (missing message)
        payload = {"status": "offline"}
        console.print(f"[magenta][Producer] Emitting Data: {payload}[/magenta]")
        return json.dumps(payload)


class ConsumerAgent:
    def process_data(self, data: dict):
        console.print(
            f"[bold green][Consumer] Successfully processing clean data: {data}[/bold green]"
        )


async def main():
    console.print("[bold cyan]--- Multi-Agent Flow with SentinelCell ---[/bold cyan]")

    producer = ProducerAgent()
    consumer = ConsumerAgent()

    # 1. Producer emits data
    raw_data = producer.emit_data()

    # 2. SentinelCell Intercepts (Middleware)
    console.print("[yellow][SentinelCell] Intercepting traffic...[/yellow]")
    sentinel = SentinelCell()
    try:
        # The Consumer (Agent_Beta) strictly expects a 'message' string alongside 'status'
        result = await sentinel.intercept(
            source="Producer", target="Agent_Beta", payload=raw_data
        )

        # 3. Consumer receives data ONLY if valid/healed
        if result:
            console.print(
                "[bold cyan][SentinelCell] Traffic cleared. Forwarding to Consumer...[/bold cyan]"
            )
            consumer.process_data(result)
        else:
            console.print(
                "[bold red][SentinelCell] Traffic blocked. Consumer protected from bad data.[/bold red]"
            )
    finally:
        await sentinel.stop()


if __name__ == "__main__":
    asyncio.run(main())
