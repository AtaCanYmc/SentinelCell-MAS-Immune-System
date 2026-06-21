import pytest
from src.skills.validation import SemanticValidator
from registry.base_contracts import StatusContract


class MockMCPClient:
    async def fetch_schema(self, agent_id: str):
        if agent_id == "Agent_Beta":
            return StatusContract.model_json_schema()
        return None


@pytest.fixture
def validator():
    return SemanticValidator(mcp_client=MockMCPClient())


@pytest.mark.asyncio
async def test_validate_packet_valid(validator):
    data = {"status": "ok", "message": "All good"}
    result = await validator.validate_packet("Agent_Beta", data)
    assert result is True


@pytest.mark.asyncio
async def test_validate_packet_invalid(validator):
    data = {"status": "ok"}  # Missing 'message'
    result = await validator.validate_packet("Agent_Beta", data)
    assert result is False


@pytest.mark.asyncio
async def test_validate_packet_no_schema(validator):
    data = {"random": "data"}
    result = await validator.validate_packet("Agent_Gamma", data)
    assert result is True
