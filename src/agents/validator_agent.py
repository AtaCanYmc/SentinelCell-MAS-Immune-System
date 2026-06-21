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

    async def process(self, target: str, data: dict) -> bool:
        console.print(f"[info][SentinelCell][/info] Validating data for {target}...")
        is_valid = await self.validator.validate_packet(target, data)
        if not is_valid:
            console.print(
                "[warning][SentinelCell][/warning] Breach detected! Triggering healing..."
            )
            # We would invoke self.healer here in a real scenario
            return False
        return True
