import pytest
from src.healer import SelfHealingEngine
from registry.base_contracts import StatusContract


@pytest.mark.asyncio
async def test_healer_mock_success():
    engine = SelfHealingEngine(api_key=None)  # Forces mock mode
    malformed_data = {"status": "ok"}  # Missing 'message'
    error_context = "Missing required field: 'message'"
    schema_json = StatusContract.model_json_schema()

    healed_data = await engine.heal_packet(schema_json, malformed_data, error_context)

    assert healed_data is not None
    assert "message" in healed_data
    assert healed_data["message"] == "Auto-healed context for status: ok"


@pytest.mark.asyncio
async def test_healer_mock_failure():
    engine = SelfHealingEngine(api_key=None)
    malformed_data = {"completely": "wrong"}
    error_context = "Missing required fields"
    schema_json = StatusContract.model_json_schema()

    # Mock healer only fixes specific things, this should fail re-validation
    healed_data = await engine.heal_packet(schema_json, malformed_data, error_context)

    assert healed_data is None
