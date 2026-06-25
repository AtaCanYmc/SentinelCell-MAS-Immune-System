import asyncio
import time
from rich.console import Console

console = Console()


class MockMCPClient:
    async def fetch_schema(self, target: str):
        return {
            "title": "Circuit Breaker Target",
            "type": "object",
            "properties": {"val": {"type": "integer"}},
            "required": ["val"],
        }


async def simulate_circuit_breaker_recovery():
    from src.core.orchestrator import SentinelOrchestrator
    from src.skills.validation import SemanticValidator
    from src.skills.repair import SelfHealingEngine
    import os

    # Force a very short cooldown for testing
    os.environ["CIRCUIT_BREAKER_COOLDOWN"] = "2"
    os.environ["CIRCUIT_BREAKER_THRESHOLD"] = "3"
    # Ensure LLM repair fails quickly to trigger breaker
    os.environ["MAX_REPAIR_ATTEMPTS"] = "0"

    validator = SemanticValidator(MockMCPClient())
    healer = SelfHealingEngine()
    orchestrator = SentinelOrchestrator(validator, healer)

    console.print(
        "[bold yellow]--- Testing Circuit Breaker Half-Open Recovery ---[/bold yellow]"
    )

    invalid_payload = '{"val": "not an int and no quotes fixing will help here because deterministic healer coerces str to int if possible, but this is letters"}'
    valid_payload = '{"val": 42}'

    # 1. Trip the breaker
    console.print("\n[dim]Tripping the breaker...[/dim]")
    for i in range(4):
        console.print(f"\n[cyan]Attempt {i+1}:[/cyan]")
        await orchestrator.intercept("spam_agent", "target", invalid_payload)

    # 2. Try while tripped
    console.print(
        "\n[dim]Trying valid payload while breaker is tripped (should fail instantly)...[/dim]"
    )
    res = await orchestrator.intercept("spam_agent", "target", valid_payload)
    if not res:
        console.print(
            "[bold green][+] Correctly rejected by tripped breaker.[/bold green]"
        )
    else:
        console.print("[bold red][!] Breaker failed to reject![/bold red]")

    # 3. Wait for cooldown
    console.print("\n[dim]Waiting 3 seconds for Half-Open cooldown...[/dim]")
    time.sleep(3)

    # 4. Try valid payload (Half-Open should succeed and close)
    console.print("\n[dim]Testing Half-Open state with valid payload...[/dim]")
    res = await orchestrator.intercept("spam_agent", "target", valid_payload)
    if res:
        console.print(
            "[bold green][+] Half-Open test succeeded! Breaker reset.[/bold green]"
        )
    else:
        console.print("[bold red][!] Half-Open test failed![/bold red]")

    # 5. Send another valid payload to prove it's fully closed (normal operation)
    console.print("\n[dim]Testing fully recovered state...[/dim]")
    res = await orchestrator.intercept("spam_agent", "target", valid_payload)
    if res:
        console.print(
            "[bold green][+] Fully closed (normal) operation verified![/bold green]"
        )
    else:
        console.print("[bold red][!] Fully closed operation failed![/bold red]")


if __name__ == "__main__":
    asyncio.run(simulate_circuit_breaker_recovery())
