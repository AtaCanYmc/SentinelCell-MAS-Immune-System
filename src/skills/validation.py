import asyncio
import jsonschema
from rich.console import Console
from rich.panel import Panel
from src.mcp_integration.client import SchemaRegistryClient

console = Console()


class SecuritySanitizer:
    MALICIOUS_PATTERNS = [
        "ignore previous",
        "system prompt",
        "external_ip",
        "eval(",
        "exec(",
    ]

    @classmethod
    def check_payload(cls, data: dict) -> str | None:
        data_str = str(data).lower()
        for pattern in cls.MALICIOUS_PATTERNS:
            if pattern in data_str:
                return f"SECURITY_BREACH: Adversarial Prompt Injection Detected (Pattern: '{pattern}')"
        return None


class SemanticValidator:
    """
    Semantic Integrity Engine based on JSON Schema (via MCP).
    """

    def __init__(self, mcp_client: SchemaRegistryClient):
        import os

        self.mcp_client = mcp_client
        self._cache = {}  # In-memory cache: {agent_target: {"schema": dict, "expires_at": float}}
        self.cache_ttl = int(os.getenv("SCHEMA_CACHE_TTL_SECONDS", "300"))

    async def _get_schema(self, agent_target: str) -> dict | None:
        import time

        now = time.time()

        if agent_target in self._cache:
            cache_entry = self._cache[agent_target]
            if now < cache_entry["expires_at"]:
                return cache_entry["schema"]

        # Fetch from MCP server
        console.print(
            f"[dim]Fetching schema from MCP Registry for {agent_target}...[/dim]"
        )
        try:
            schema = await self.mcp_client.fetch_schema(agent_target)
        except Exception as e:
            import os

            policy = os.getenv("MCP_FAILURE_POLICY", "FAIL_OPEN").upper()
            if policy == "FAIL_CLOSED":
                console.print(
                    f"[bold red][!] MCP Registry Error: {e}. FAIL_CLOSED engaged. Blocking traffic.[/bold red]"
                )
                raise RuntimeError("MCP_FAILURE")
            else:
                console.print(
                    f"[bold red][!] MCP Registry Error: {e}. Fail-Open engaged, passing traffic.[/bold red]"
                )
                return None

        # Update cache
        self._cache[agent_target] = {
            "schema": schema,
            "expires_at": now + self.cache_ttl,
        }
        return schema

    def clear_cache(self, agent_target: str = None):
        """
        Clears the schema cache. If agent_target is provided, clears only that target.
        """
        if agent_target:
            self._cache.pop(agent_target, None)
            console.print(
                f"[dim cyan][*] Cache cleared for agent: {agent_target}[/dim cyan]"
            )
        else:
            self._cache.clear()
            console.print("[dim cyan][*] Schema cache completely purged[/dim cyan]")

    async def validate_packet(self, agent_target: str, data: dict) -> bool:
        """
        Validates the incoming data against the target agent's schema.
        Returns True if valid, False if invalid.
        Raises ValueError if no schema is found but we expect one, though for now we pass through.
        """
        try:
            schema = await self._get_schema(agent_target)
        except RuntimeError:
            return False

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
        # 1. Get Schema
        try:
            schema = await self._get_schema(agent_target)
        except RuntimeError:
            return False, None, "MCP Registry Unavailable"

        if not schema:
            return True, None, None

        # 2. Active Security Shield (Sanitizer)
        from src.core.broadcaster import broadcaster

        security_error = SecuritySanitizer.check_payload(data)
        if security_error:
            await broadcaster.broadcast("SECURITY_ALERT", security_error)
            return False, schema, security_error

        # 3. Schema Validation
        try:
            jsonschema.validate(instance=data, schema=schema)
            return True, schema, None
        except jsonschema.ValidationError as e:
            return False, schema, e.message

    async def validate_node(self, state: dict) -> dict:
        """
        LangGraph node execution for validation.
        """
        target = state.get("agent_target", "")
        data = state.get("payload", {})
        console.print(f"[info][SentinelCell][/info] Validating data for {target}...")
        is_valid, schema, error_context = await self.validate_and_get_schema(
            target, data
        )
        if not is_valid:
            console.print(
                Panel(
                    f"[bold red]Validation Error:[/bold red]\n{error_context}",
                    title="[!] Schema Mismatch",
                    border_style="red",
                )
            )
        return {
            "is_valid": is_valid,
            "schema_dict": schema,
            "error_context": error_context,
        }
