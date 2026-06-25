import asyncio
from rich.console import Console

console = Console()


class MockMCPClient:
    async def fetch_schema(self, target: str):
        return {
            "title": "TradingBotTarget",
            "type": "object",
            "properties": {"asset": {"type": "string"}, "amount": {"type": "integer"}},
            "required": ["asset", "amount"],
        }


async def simulate_financial_anomaly():
    from src.core.orchestrator import SentinelOrchestrator
    from src.skills.validation import SemanticValidator
    from src.skills.repair import SelfHealingEngine

    validator = SemanticValidator(MockMCPClient())
    healer = SelfHealingEngine()
    orchestrator = SentinelOrchestrator(validator, healer)

    console.print(
        "[bold yellow]--- Testing Financial Drift Guard (Anomaly Detection) ---[/bold yellow]"
    )

    agent = "trading_agent"

    # Send baseline transactions (Window size is 10, but needs at least 3 to calculate mean)
    baselines = [500, 520, 480, 510, 490]

    for val in baselines:
        payload = f'{{"asset": "AAPL", "amount": {val}}}'
        console.print(f"[dim]Sending baseline transaction: {payload}[/dim]")
        res = await orchestrator.intercept(agent, "target", payload)
        if res:
            console.print("[green][+] Valid transaction passed.[/green]")

    # Send an anomalous transaction
    console.print(
        "\n[bold red][!] Attempting logical drift attack (Wallet Drain)...[/bold red]"
    )
    anomaly_payload = '{"asset": "AAPL", "amount": 50000}'
    console.print(f"[dim]Sending anomaly transaction: {anomaly_payload}[/dim]")

    res = await orchestrator.intercept(agent, "target", anomaly_payload)
    if res is None:
        console.print(
            "[bold green][+] Anomaly caught and dropped successfully![/bold green]"
        )
    else:
        console.print("[bold red][!] System failed to catch the anomaly.[/bold red]")


if __name__ == "__main__":
    asyncio.run(simulate_financial_anomaly())
