from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel
import asyncio

console = Console()


class SemanticValidator:
    """
    Semantic Integrity Engine based on Pydantic.
    """

    def __init__(self, schema_registry: dict):
        # schema_registry is a mapping of agent target ID to Pydantic models
        self.schema_registry = schema_registry

    async def validate_packet(self, agent_target: str, data: dict) -> bool:
        """
        Validates the incoming data against the target agent's schema.
        """
        schema = self.schema_registry.get(agent_target)
        if not schema:
            console.print(
                f"[dim yellow][?] No contract found for target: {agent_target}. Bypassing validation.[/dim yellow]"
            )
            return True  # Pass through if no contract exists

        try:
            # Simulate non-intrusive fast processing
            await asyncio.sleep(0.005)
            schema(**data)
            return True
        except ValidationError as e:
            console.print(
                Panel(
                    f"[bold red]Validation Error:[/bold red]\n{e}",
                    title="[!] Schema Mismatch",
                    border_style="red",
                )
            )
            return False
