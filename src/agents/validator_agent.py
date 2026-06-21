import os
from src.skills.validation import SemanticValidator
from src.skills.repair import SelfHealingEngine
from src.core.logger import get_console
from src.mcp_integration.client import SchemaRegistryClient
from src.core.orchestrator import SentinelOrchestrator

console = get_console()


class SentinelCell:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        registry_path = os.path.join(
            current_dir, "..", "mcp_integration", "registry.py"
        )
        self.mcp_client = SchemaRegistryClient(server_script_path=registry_path)

        self.validator = SemanticValidator(mcp_client=self.mcp_client)
        self.healer = SelfHealingEngine()

        # Instantiate the LangGraph Orchestrator
        self.orchestrator = SentinelOrchestrator(self.validator, self.healer)

    async def intercept(self, source: str, target: str, payload: str) -> dict | None:
        """
        Entry point for intercepting and routing traffic through the MAS Immune System.
        """
        return await self.orchestrator.intercept(source, target, payload)
