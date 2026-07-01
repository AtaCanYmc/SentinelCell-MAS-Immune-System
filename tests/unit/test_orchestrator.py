import pytest
import json
from src.core.orchestrator import SentinelOrchestrator


@pytest.fixture(autouse=True)
def mock_redis_dict_proxy(monkeypatch):
    db = {}

    class MockRedisDictProxy:
        def __init__(self, namespace, redis_url=None):
            self.namespace = namespace

        async def get(self, k, default=None):
            return db.get(f"{self.namespace}:{k}", default)

        async def set(self, k, v):
            db[f"{self.namespace}:{k}"] = v

        async def exists(self, k) -> bool:
            return f"{self.namespace}:{k}" in db

        async def items(self):
            res = {}
            for key, val in db.items():
                if key.startswith(f"{self.namespace}:"):
                    short_k = key[len(f"{self.namespace}:") :]
                    res[short_k] = val
            return res

    monkeypatch.setattr("src.core.orchestrator.RedisDictProxy", MockRedisDictProxy)


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
