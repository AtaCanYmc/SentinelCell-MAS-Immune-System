import asyncio
import os
from rich.console import Console
from util import setup_mock_environment

setup_mock_environment()

console = Console()


class MockMCPClient:
    async def fetch_schema(self, target: str):
        return {
            "title": "HITL_Target",
            "type": "object",
            "properties": {"critical_action": {"type": "boolean"}},
            "required": ["critical_action"],
        }


async def simulate_hitl():
    # Enable HITL Mode
    os.environ["HITL_ENABLED"] = "true"

    from src.core.orchestrator import SentinelOrchestrator
    from src.skills.validation import SemanticValidator
    from src.skills.repair import SelfHealingEngine

    validator = SemanticValidator(MockMCPClient())
    healer = SelfHealingEngine()
    orchestrator = SentinelOrchestrator(validator, healer)

    console.print(
        "[bold yellow]--- Testing Human-in-the-Loop Approval ---[/bold yellow]"
    )

    payload = '{"critical_action": "yes"}'  # Deterministic healer will fix this, wait.
    payload = '{"critical_action": true, "extra": "broken_field'  # Needs LLM

    # We mock the builtins.input function so the test runs automatically but demonstrates the branch
    import builtins

    async def run_with_mock_input(mock_reply):
        original_input = builtins.input
        builtins.input = lambda prompt: mock_reply
        try:
            console.print(
                f"\n[cyan]Simulating Human Operator answering: '{mock_reply}'[/cyan]"
            )
            res = await orchestrator.intercept("agent_h", "target", payload)
            if res:
                console.print(
                    "[bold green][+] Payload processed successfully.[/bold green]"
                )
            else:
                console.print("[bold red][!] Payload dropped.[/bold red]")
        finally:
            builtins.input = original_input

    # 1. Operator Approves
    await run_with_mock_input("y")

    # Reset circuit breaker just in case
    orchestrator.agent_circuit_breakers.clear()

    # 2. Operator Rejects
    await run_with_mock_input("n")


if __name__ == "__main__":
    asyncio.run(simulate_hitl())
