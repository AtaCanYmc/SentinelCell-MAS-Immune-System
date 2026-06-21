import pytest
import json
from src.listener import TrafficSniffer


@pytest.mark.asyncio
async def test_intercept_valid_json():
    # Mock validation callback returning True
    async def mock_validator(target: str, data: dict) -> bool:
        return True

    sniffer = TrafficSniffer(validation_callback=mock_validator)
    payload = json.dumps({"test": "data"})
    result = await sniffer.intercept("Agent_A", "Agent_B", payload)

    assert result == {"test": "data"}


@pytest.mark.asyncio
async def test_intercept_malformed_json():
    sniffer = TrafficSniffer()
    payload = "{malformed_json:"
    result = await sniffer.intercept("Agent_A", "Agent_B", payload)

    # Should return None for malformed JSON, rather than raising an exception
    assert result is None


@pytest.mark.asyncio
async def test_intercept_validation_failure():
    # Mock validation callback returning False
    async def mock_validator(target: str, data: dict) -> bool:
        return False

    sniffer = TrafficSniffer(validation_callback=mock_validator)
    payload = json.dumps({"test": "data"})
    result = await sniffer.intercept("Agent_A", "Agent_B", payload)

    # Should still return data for now (healing will be implemented later)
    assert result == {"test": "data"}
