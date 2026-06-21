import asyncio
import jsonschema
from rich.console import Console
from rich.panel import Panel
from src.mcp_integration.client import SchemaRegistryClient

console = Console()


class SemanticValidator:
    """
    Semantic Integrity Engine based on JSON Schema (via MCP).
    """

    def __init__(self, mcp_client: SchemaRegistryClient):
        self.mcp_client = mcp_client
        self._cache = {}  # In-memory cache for ultra-fast near-instant validation

    async def _get_schema(self, agent_target: str) -> dict | None:
        if agent_target in self._cache:
            return self._cache[agent_target]

        # Fetch from MCP server
        console.print(
            f"[dim]Fetching schema from MCP Registry for {agent_target}...[/dim]"
        )
        schema = await self.mcp_client.fetch_schema(agent_target)
        self._cache[agent_target] = schema
        return schema

    async def validate_packet(self, agent_target: str, data: dict) -> bool:
        """
        Validates the incoming data against the target agent's schema.
        Returns True if valid, False if invalid.
        Raises ValueError if no schema is found but we expect one, though for now we pass through.
        """
        schema = await self._get_schema(agent_target)
        if not schema:
            console.print(
                f"[dim yellow][?] No contract found for target: {agent_target}. Bypassing validation.[/dim yellow]"
            )
            return True  # Pass through if no contract exists

        try:
            # Simulate non-intrusive fast processing
            await asyncio.sleep(0.005)
            jsonschema.validate(instance=data, schema=schema)
            return True
        except jsonschema.ValidationError as e:
            console.print(
                Panel(
                    f"[bold red]Validation Error:[/bold red]\n{e.message}",
                    title="[!] Schema Mismatch",
                    border_style="red",
                )
            )
            return False

    async def validate_and_get_schema(
        self, agent_target: str, data: dict
    ) -> tuple[bool, dict | None, str | None]:
        """
        Helper for healer: Returns (is_valid, schema_dict, error_context)
        """
        schema = await self._get_schema(agent_target)
        if not schema:
            return True, None, None

        try:
            jsonschema.validate(instance=data, schema=schema)
            return True, schema, None
        except jsonschema.ValidationError as e:
            return False, schema, e.message
