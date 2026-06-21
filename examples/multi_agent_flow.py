import asyncio
from rich.console import Console
from src.core.orchestrator import SentinelOrchestrator

console = Console()


class ProducerAgent:
    def emit_data(self):
        # Emitting malformed data intentionally (missing timestamp)
        payload = {"data_value": 42, "user": "admin"}
        console.print(f"[magenta][Producer] Emitting Data: {payload}[/magenta]")
        return payload


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
    orchestrator = SentinelOrchestrator()
    graph = orchestrator.compile()

    # The Consumer strictly expects a 'timestamp' string alongside 'data_value'
    strict_schema = {
        "type": "object",
        "properties": {
            "data_value": {"type": "integer"},
            "timestamp": {"type": "string"},
        },
        "required": ["data_value", "timestamp"],
    }

    state = {
        "payload": raw_data,
        "schema_dict": strict_schema,
        "repair_attempts": 0,
        "error_context": "",
        "active_provider": "",
    }

    result = await graph.ainvoke(state)

    # 3. Consumer receives data ONLY if valid/healed
    if "payload" in result and result.get("error_context") == "":
        console.print(
            "[bold cyan][SentinelCell] Traffic cleared. Forwarding to Consumer...[/bold cyan]"
        )
        consumer.process_data(result["payload"])
    else:
        console.print(
            "[bold red][SentinelCell] Traffic blocked. Consumer protected from bad data.[/bold red]"
        )


if __name__ == "__main__":
    asyncio.run(main())
