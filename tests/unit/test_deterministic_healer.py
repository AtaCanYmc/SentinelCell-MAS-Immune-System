import pytest
from src.skills.deterministic_healer import DeterministicHealer


@pytest.mark.asyncio
async def test_deterministic_healer_raw_payload():
    healer = DeterministicHealer()
    state = {"payload": {"_raw_unparsed_payload": "{'test': 'value'}"}}
    result = await healer.repair_node(state)
    assert result["payload"] == {"test": "value"}
    assert result["active_provider"] == "DETERMINISTIC_RULE_ENGINE"
    assert result["deterministic_repair_attempts"] == 1


@pytest.mark.asyncio
async def test_deterministic_healer_raw_payload_fail():
    healer = DeterministicHealer()
    state = {
        "payload": {
            "_raw_unparsed_payload": "{'test': value"  # Invalid
        }
    }
    result = await healer.repair_node(state)
    assert "_raw_unparsed_payload" in result["payload"]


@pytest.mark.asyncio
async def test_deterministic_healer_type_coercion():
    healer = DeterministicHealer()
    state = {
        "payload": {
            "int_val": "123",
            "float_val": "12.3",
            "str_val": 456,
            "bool_val": "true",
            "bool_val2": "0",
            "invalid_int": "abc",
            "invalid_float": "abc",
        },
        "schema_dict": {
            "properties": {
                "int_val": {"type": "integer"},
                "float_val": {"type": "number"},
                "str_val": {"type": "string"},
                "bool_val": {"type": "boolean"},
                "bool_val2": {"type": "boolean"},
                "invalid_int": {"type": "integer"},
                "invalid_float": {"type": "number"},
            }
        },
    }
    result = await healer.repair_node(state)

    assert result["payload"]["int_val"] == 123
    assert result["payload"]["float_val"] == 12.3
    assert result["payload"]["str_val"] == "456"
    assert result["payload"]["bool_val"] is True
    assert result["payload"]["bool_val2"] is False
    assert result["payload"]["invalid_int"] == "abc"  # Fails to coerce
    assert result["payload"]["invalid_float"] == "abc"  # Fails to coerce
    assert result["active_provider"] == "DETERMINISTIC_RULE_ENGINE"


@pytest.mark.asyncio
async def test_deterministic_healer_no_schema():
    healer = DeterministicHealer()
    state = {
        "payload": {"test": "val"},
    }
    result = await healer.repair_node(state)
    assert result["payload"] == {"test": "val"}
    assert "active_provider" not in result
