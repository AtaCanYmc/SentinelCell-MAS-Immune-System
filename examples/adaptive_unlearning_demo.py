import asyncio
from src.mcp_integration.client import SchemaRegistryClient
from src.skills.validation import SemanticValidator
from src.skills.repair import SelfHealingEngine
from rich.console import Console

console = Console()


async def main():
    validator = SemanticValidator(
        SchemaRegistryClient("src/mcp_integration/registry.py")
    )
    healer = SelfHealingEngine()

    await validator.mcp_client.register_schema(
        "ProfileUpdate",
        {
            "title": "Profile",
            "type": "object",
            "properties": {"age": {"type": "integer"}},
            "required": ["age"],
        },
    )

    # Simulating the orchestrator loop by passing last_memory_id to the repair node manually
    state = {
        "schema_dict": {
            "title": "Profile",
            "type": "object",
            "properties": {"age": {"type": "integer"}},
        },
        "payload": {"age": "twenty"},
        "repair_attempts": 1,
        "error_context": "age must be integer",
        "last_memory_id": "mem-hallucination-1234",
    }

    console.print(
        "[bold yellow][*] Injecting hallucinated memory ID into state...[/bold yellow]"
    )

    console.print(
        "[bold cyan][*] Triggering repair node with failed last_memory_id...[/bold cyan]"
    )
    await healer.repair_node(state)

    console.print(
        "[bold green][+] Demo completed. Check logs above for UNLEARNING action.[/bold green]"
    )


if __name__ == "__main__":
    asyncio.run(main())
