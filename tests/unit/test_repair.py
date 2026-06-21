import pytest
from unittest.mock import patch, MagicMock
from src.skills.repair import SelfHealingEngine


@pytest.mark.asyncio
@patch("src.skills.repair.LLMFactory")
async def test_healer_repair_node_success(mock_factory):
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = '{"status": "ok", "message": "healed"}'

    async def mock_ainvoke(*args, **kwargs):
        return mock_response

    mock_llm.ainvoke = mock_ainvoke
    mock_factory.get_llm.return_value = mock_llm

    engine = SelfHealingEngine()

    # Need to patch _log_decision so we don't write to real files in tests
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
        mock_log.assert_called_once()


@pytest.mark.asyncio
@patch("src.skills.repair.LLMFactory")
async def test_healer_repair_node_failure(mock_factory):
    mock_llm = MagicMock()

    async def mock_ainvoke(*args, **kwargs):
        raise Exception("LLM Timeout")

    mock_llm.ainvoke = mock_ainvoke
    mock_factory.get_llm.return_value = mock_llm

    engine = SelfHealingEngine()

    state = {
        "repair_attempts": 1,
        "schema_dict": {"title": "TestSchema"},
        "payload": {"status": "ok"},
        "error_context": "Missing message",
    }

    result = await engine.repair_node(state)

    # Fallback uses attempts % len(providers) -> 1 % 3 -> index 1 -> LOCAL_OLLAMA
    assert "payload" not in result
    assert result["active_provider"] == "LOCAL_OLLAMA"
    assert result["repair_attempts"] == 2
