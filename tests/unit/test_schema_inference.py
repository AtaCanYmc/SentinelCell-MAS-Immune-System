import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.skills.schema_inference import AutoSchemaInferencer


@pytest.fixture
def mock_mcp_client():
    client = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_auto_schema_inferencer_threshold_not_met(mock_mcp_client, monkeypatch):
    monkeypatch.setenv("OBSERVATION_THRESHOLD", "3")

    with patch("src.skills.schema_inference.LLMFactory.get_llm") as mock_get_llm:
        mock_llm = AsyncMock()
        mock_get_llm.return_value = mock_llm
        inferencer = AutoSchemaInferencer(mcp_client=mock_mcp_client)

        # Observe 2 payloads (below threshold 3)
        inferencer.observe("test_agent", {"field": "value1"})
        inferencer.observe("test_agent", {"field": "value2"})

        assert "test_agent" in inferencer._observations
        assert len(inferencer._observations["test_agent"]) == 2
        assert "test_agent" not in inferencer._inferring


@pytest.mark.asyncio
async def test_auto_schema_inferencer_threshold_met_success(
    mock_mcp_client, monkeypatch
):
    monkeypatch.setenv("OBSERVATION_THRESHOLD", "2")

    with patch("src.skills.schema_inference.LLMFactory.get_llm") as mock_get_llm:
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = '```json\n{"type": "object", "properties": {"field": {"type": "string"}}}\n```'
        mock_llm.ainvoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        mock_cb = MagicMock()
        mock_mcp_client.register_schema.return_value = True

        inferencer = AutoSchemaInferencer(
            mcp_client=mock_mcp_client, on_schema_registered_cb=mock_cb
        )

        # Observe 2 payloads to trigger threshold
        inferencer.observe("test_agent", {"field": "value1"})
        inferencer.observe("test_agent", {"field": "value2"})

        # Wait for background task to complete
        await asyncio.sleep(0.1)

        # Assertions
        assert "test_agent" not in inferencer._observations
        assert "test_agent" not in inferencer._inferring
        mock_mcp_client.register_schema.assert_called_once()
        mock_cb.assert_called_once_with("test_agent")


@pytest.mark.asyncio
async def test_auto_schema_inferencer_llm_failure(mock_mcp_client, monkeypatch):
    monkeypatch.setenv("OBSERVATION_THRESHOLD", "1")

    with patch("src.skills.schema_inference.LLMFactory.get_llm") as mock_get_llm:
        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "INVALID_JSON_RESPONSE"
        mock_llm.ainvoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        inferencer = AutoSchemaInferencer(mcp_client=mock_mcp_client)
        inferencer.observe("test_agent_fail", {"field": "value1"})

        await asyncio.sleep(0.1)

        # Inference failed
        mock_mcp_client.register_schema.assert_not_called()
        assert "test_agent_fail" not in inferencer._inferring
