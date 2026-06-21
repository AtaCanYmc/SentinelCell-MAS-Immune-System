import os
import pytest
from src.mcp_client import SchemaRegistryClient
from src.validator import SemanticValidator


@pytest.mark.asyncio
async def test_mcp_integration_flow():
    # Construct absolute path to mcp_server.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(current_dir, "..", "..", "src", "mcp_server.py")

    client = SchemaRegistryClient(server_script_path=server_script)
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
