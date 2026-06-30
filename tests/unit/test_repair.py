import pytest
from unittest.mock import patch, MagicMock
from src.skills.repair import SelfHealingEngine


@pytest.fixture(autouse=True)
def mock_redis_env(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)


@pytest.mark.asyncio
@patch("src.skills.repair.LLMFactory")
async def test_healer_repair_node_success(mock_factory):
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = '```json\n{"status": "ok", "message": "healed"}\n```'

    async def mock_ainvoke(*args, **kwargs):
        return mock_response

    mock_llm.ainvoke = mock_ainvoke
    mock_factory.get_llm.return_value = mock_llm

    engine = SelfHealingEngine()
    engine.providers = ["OPENAI", "LOCAL_OLLAMA", "ANTHROPIC"]

    # Mock memory store
    mock_memory = MagicMock()
    mock_memory.query_memory.return_value = "past memory"
    engine.memory = mock_memory

    with patch.object(engine, "_log_decision") as mock_log:
        state = {
            "repair_attempts": 0,
            "schema_dict": {"title": "TestSchema"},
            "payload": {"status": "ok"},
            "error_context": "Missing message",
        }

        result = await engine.repair_node(state)

        assert result["payload"] == {"status": "ok", "message": "healed"}
        assert result["active_provider"] == "OPENAI"
        assert result["repair_attempts"] == 1
        assert result["last_memory_id"] is not None
        mock_log.assert_called_once()
        mock_memory.query_memory.assert_called_once()
        mock_memory.add_memory.assert_called_once()


@pytest.mark.asyncio
@patch("src.skills.repair.LLMFactory")
async def test_healer_repair_node_failure(mock_factory):
    mock_llm = MagicMock()

    async def mock_ainvoke(*args, **kwargs):
        raise Exception("LLM Timeout")

    mock_llm.ainvoke = mock_ainvoke
    mock_factory.get_llm.return_value = mock_llm

    engine = SelfHealingEngine()
    engine.providers = ["OPENAI", "LOCAL_OLLAMA", "ANTHROPIC"]

    state = {
        "repair_attempts": 1,
        "schema_dict": {"title": "TestSchema"},
        "payload": {"status": "ok"},
        "error_context": "Missing message",
    }

    result = await engine.repair_node(state)

    assert "payload" not in result
    assert result["active_provider"] == "LOCAL_OLLAMA"
    assert result["repair_attempts"] == 2
    assert result["last_memory_id"] is None


@pytest.mark.asyncio
@patch("src.skills.repair.LLMFactory")
async def test_healer_repair_node_unlearning(mock_factory):
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = '```json\n{"status": "ok", "message": "healed again"}\n```'

    async def mock_ainvoke(*args, **kwargs):
        return mock_response

    mock_llm.ainvoke = mock_ainvoke
    mock_factory.get_llm.return_value = mock_llm

    engine = SelfHealingEngine()

    mock_memory = MagicMock()
    mock_memory.query_memory.return_value = None
    engine.memory = mock_memory

    with patch.object(engine, "_log_decision"):
        state = {
            "repair_attempts": 1,
            "schema_dict": {"title": "TestSchema"},
            "payload": {"status": "ok"},
            "error_context": "Missing message",
            "last_memory_id": "mem-12345",
        }

        result = await engine.repair_node(state)

        # It should delete the last memory
        mock_memory.delete_memory.assert_called_once_with("mem-12345")
        assert result["last_memory_id"] is not None
        assert result["last_memory_id"].startswith("mem-")


@pytest.mark.asyncio
@patch("src.skills.repair.LLMFactory")
async def test_healer_repair_node_semantic_drift(mock_factory):
    mock_llm = MagicMock()
    mock_response = MagicMock()
    # LLM hallucinates and drops critical original data
    mock_response.content = '```json\n{"status": "ok"}\n```'

    async def mock_ainvoke(*args, **kwargs):
        return mock_response

    mock_llm.ainvoke = mock_ainvoke
    mock_factory.get_llm.return_value = mock_llm

    engine = SelfHealingEngine()
    engine.memory = None

    state = {
        "repair_attempts": 0,
        "schema_dict": {"title": "TestSchema"},
        # Original payload had critical info
        "payload": {"critical_id": 12345, "amount": 999.99},
        "error_context": "Missing status",
    }

    # Since the healed payload has no overlap with the original atomic values, it will trigger Semantic Drift
    result = await engine.repair_node(state)

    # Semantic Drift Error causes healing to fail
    assert "payload" not in result
    assert result["repair_attempts"] == 1


@pytest.mark.asyncio
async def test_healer_repair_node_rate_limit():
    from unittest.mock import AsyncMock

    with patch(
        "os.getenv",
        side_effect=lambda k, d=None: (
            "redis://localhost:6379" if k == "REDIS_URL" else d
        ),
    ):
        with patch("redis.asyncio.from_url") as mock_redis_func:
            mock_redis = MagicMock()
            mock_redis.incr = AsyncMock(return_value=100)  # Exceeds rate limit
            mock_redis.expire = AsyncMock()
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.__aenter__ = AsyncMock(return_value=mock_redis)
            mock_redis.__aexit__ = AsyncMock(return_value=None)
            mock_redis_func.return_value = mock_redis

            engine = SelfHealingEngine()
            state = {
                "repair_attempts": 0,
                "schema_dict": {"title": "TestSchema"},
                "payload": {"status": "ok"},
                "error_context": "Missing message",
            }

            result = await engine.repair_node(state)
            assert result["is_valid"] is False
            assert "Rate Limit Exceeded" in result["error_context"]
