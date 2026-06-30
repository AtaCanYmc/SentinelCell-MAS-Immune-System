import asyncio
import json
from rich.console import Console
from util import setup_mock_environment

setup_mock_environment()

console = Console()


class MockMCPClient:
    async def fetch_schema(self, target: str):
        return {
            "title": "V2 Schema",
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "status": {"type": "string"},
                "count": {"type": "integer"},
            },
            "required": ["id", "status", "count"],
        }


async def simulate_schema_evolution():
    from src.core.orchestrator import SentinelOrchestrator
    from src.skills.validation import SemanticValidator
    from src.skills.repair import SelfHealingEngine

    validator = SemanticValidator(MockMCPClient())
    healer = SelfHealingEngine()
    orchestrator = SentinelOrchestrator(validator, healer)

    console.print(
        "[bold yellow]--- Testing Schema Evolution & Deterministic Repair ---[/bold yellow]"
    )

    # Send v1 payload: missing 'status', and 'count' is a string instead of integer
    v1_payload = {
        "id": "agent-123",
        "count": "42",  # Deterministic healer should coerce this to int
    }

    raw_payload = json.dumps(v1_payload)
    console.print(f"Sending V1 Payload: {raw_payload}")

    # Note: If it's missing a required field ("status"), the deterministic healer can't invent it,
    # so it will fall back to the LLM healer to complete the schema evolution contextually.

    result = await orchestrator.intercept("legacy_agent", "v2_target", raw_payload)

    if result:
        console.print(f"[bold green][+] Evolved Payload: {result}[/bold green]")
    else:
        console.print("[bold red][!] Schema evolution failed[/bold red]")


if __name__ == "__main__":
    asyncio.run(simulate_schema_evolution())
