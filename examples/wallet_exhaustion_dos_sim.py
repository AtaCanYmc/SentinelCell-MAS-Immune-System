import asyncio
import os
from rich.console import Console

console = Console()


class MockMCPClient:
    async def fetch_schema(self, target: str):
        return {
            "title": "Wallet Target",
            "type": "object",
            "properties": {"amount": {"type": "integer"}},
            "required": ["amount"],
        }


async def simulate_wallet_exhaustion():
    from src.core.orchestrator import SentinelOrchestrator
    from src.skills.validation import SemanticValidator
    from src.skills.repair import SelfHealingEngine

    # Set rate limit strictly low for the test
    os.environ["LLM_RATE_LIMIT_PER_MIN"] = "3"

    validator = SemanticValidator(MockMCPClient())
    healer = SelfHealingEngine()
    orchestrator = SentinelOrchestrator(validator, healer)

    console.print(
        "[bold yellow]--- Testing Wallet Exhaustion DoS Simulation ---[/bold yellow]"
    )

    payload = '{"amount": "broken"}'

    for i in range(5):
        console.print(f"\n[cyan]Sending packet {i+1}...[/cyan]")
        await orchestrator.intercept("malicious_agent", "target", payload)


if __name__ == "__main__":
    asyncio.run(simulate_wallet_exhaustion())
