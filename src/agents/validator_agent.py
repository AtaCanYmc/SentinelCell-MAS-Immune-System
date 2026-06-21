import os
from src.skills.validation import SemanticValidator
from src.skills.repair import SelfHealingEngine
from src.core.logger import get_console
from src.mcp_integration.client import SchemaRegistryClient

console = get_console()


class SentinelCell:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        registry_path = os.path.join(
            current_dir, "..", "mcp_integration", "registry.py"
        )
        self.mcp_client = SchemaRegistryClient(server_script_path=registry_path)
        self.validator = SemanticValidator(mcp_client=self.mcp_client)
        # Initialize SelfHealingEngine with a dummy key for testing
        self.healer = SelfHealingEngine(api_key="dummy_key_for_testing")
        self.healer.mock_mode = True

    async def process(self, target: str, data: dict) -> bool:
        console.print(f"[info][SentinelCell][/info] Validating data for {target}...")
        is_valid, schema, error_context = await self.validator.validate_and_get_schema(
            target, data
        )
        if not is_valid:
            console.print(
                "[warning][SentinelCell][/warning] Breach detected! Triggering healing..."
            )
            healed_data = await self.healer.heal_packet(schema, data, error_context)
            if healed_data:
                return True
            return False
        return True
