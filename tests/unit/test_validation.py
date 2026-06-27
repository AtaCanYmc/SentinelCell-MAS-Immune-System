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
    assert result is False


@pytest.mark.asyncio
async def test_validate_packet_no_schema_observation_mode(validator, monkeypatch):
    monkeypatch.setenv("OBSERVATION_MODE", "true")
    data = {"random": "data"}
    result = await validator.validate_packet("Agent_Gamma", data)
    assert result is True


@pytest.mark.asyncio
async def test_validate_packet_circuit_breaker():
    # MCP raises Exception, should use stale cache
    class MockFailingMCPClient:
        async def fetch_schema(self, agent_id: str):
            raise Exception("Network Error")

    validator = SemanticValidator(mcp_client=MockFailingMCPClient())
    validator._cache["Agent_Stale"] = {
        "schema": {
            "title": "Stale",
            "type": "object",
            "properties": {"val": {"type": "string"}},
            "required": ["val"],
        },
        "expires_at": 0,
    }  # Expired

    # Valid data according to stale cache
    data = {"val": "hello"}
    result = await validator.validate_packet("Agent_Stale", data)
    assert result is True

    # Invalid data according to stale cache
    data_bad = {"bad": "data"}
    result_bad = await validator.validate_packet("Agent_Stale", data_bad)
    assert result_bad is False
