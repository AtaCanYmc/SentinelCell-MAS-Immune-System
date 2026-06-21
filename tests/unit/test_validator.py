import pytest
from src.validator import SemanticValidator
from registry.base_contracts import StatusContract


@pytest.fixture
def validator():
    # Mock schema registry
    registry = {"Agent_Beta": StatusContract}
    return SemanticValidator(schema_registry=registry)


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
    # Agent_Gamma has no contract in the registry
    result = await validator.validate_packet("Agent_Gamma", data)
    assert result is True
