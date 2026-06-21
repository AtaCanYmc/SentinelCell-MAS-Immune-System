import pytest
import json
from src.core.orchestrator import SentinelOrchestrator


class MockValidatorPass:
    async def validate_node(self, state):
        state["is_valid"] = True
        return state


class MockValidatorFail:
    async def validate_node(self, state):
        state["is_valid"] = False
        return state


class MockHealer:
    async def repair_node(self, state):
        state["repair_attempts"] = state.get("repair_attempts", 0) + 1
        return state


@pytest.mark.asyncio
async def test_intercept_valid_json():
    orchestrator = SentinelOrchestrator(
        validator=MockValidatorPass(), healer=MockHealer()
    )
    payload = json.dumps({"test": "data"})
    result = await orchestrator.intercept("Agent_A", "Agent_B", payload)
    assert result == {"test": "data"}


@pytest.mark.asyncio
async def test_intercept_malformed_json():
    orchestrator = SentinelOrchestrator(
        validator=MockValidatorFail(), healer=MockHealer()
    )
    payload = "{malformed_json:"
    result = await orchestrator.intercept("Agent_A", "Agent_B", payload)
    # Should drop after max retries and return None
    assert result is None


@pytest.mark.asyncio
async def test_intercept_validation_failure():
    orchestrator = SentinelOrchestrator(
        validator=MockValidatorFail(), healer=MockHealer()
    )
    payload = json.dumps({"test": "data"})
    result = await orchestrator.intercept("Agent_A", "Agent_B", payload)
    assert result is None
