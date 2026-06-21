import os
import pytest
from src.mcp_integration.client import SchemaRegistryClient
from src.skills.validation import SemanticValidator


@pytest.mark.asyncio
async def test_mcp_integration_flow():
    # Construct absolute path to registry.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(
        current_dir, "..", "..", "src", "mcp_integration", "registry.py"
    )

    # Force the spawned MCP server to use IN_MEMORY registry to prevent connection refused
    env = {"SCHEMA_REGISTRY_PROVIDER": "IN_MEMORY"}

    client = SchemaRegistryClient(server_script_path=server_script, env_override=env)
    validator = SemanticValidator(mcp_client=client)

    # Valid payload
    data_valid = {"status": "ok", "message": "Success"}
    is_valid = await validator.validate_packet("Agent_Beta", data_valid)
    assert is_valid is True

    # Invalid payload
    data_invalid = {"status": "error"}
    is_valid = await validator.validate_packet("Agent_Beta", data_invalid)
    assert is_valid is False

    # No schema payload
    is_valid = await validator.validate_packet("Agent_Gamma", {"anything": "goes"})
    assert is_valid is True
