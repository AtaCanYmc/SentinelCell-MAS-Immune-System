import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.core.chat_tools import get_chat_tools


@pytest.mark.asyncio
async def test_get_operation_mode_active(monkeypatch):
    monkeypatch.delenv("PASSIVE_MONITORING", raising=False)
    tools = get_chat_tools(None)
    get_op_mode_tool = next(t for t in tools if t.name == "get_operation_mode")

    result = get_op_mode_tool.invoke({"reason": "test"})
    assert "Guardian Mode" in result


@pytest.mark.asyncio
async def test_get_operation_mode_passive(monkeypatch):
    monkeypatch.setenv("PASSIVE_MONITORING", "true")
    tools = get_chat_tools(None)
    get_op_mode_tool = next(t for t in tools if t.name == "get_operation_mode")

    result = get_op_mode_tool.invoke({"reason": "test"})
    assert "Sniffer Mode" in result


@pytest.mark.asyncio
async def test_get_llm_metrics_success():
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=b"10")

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        tools = get_chat_tools(None)
        get_metrics_tool = next(t for t in tools if t.name == "get_llm_metrics")
        result = await get_metrics_tool.ainvoke({"reason": "test"})
        assert "10 / 50" in result


@pytest.mark.asyncio
async def test_get_llm_metrics_failure():
    with patch(
        "redis.asyncio.from_url", side_effect=Exception("Redis connection error")
    ):
        tools = get_chat_tools(None)
        get_metrics_tool = next(t for t in tools if t.name == "get_llm_metrics")
        result = await get_metrics_tool.ainvoke({"reason": "test"})
        assert "Error retrieving LLM metrics" in result


def test_get_agent_circuit_breakers_empty():
    mock_sentinel = MagicMock()
    mock_sentinel.orchestrator.agent_circuit_breakers = {}

    tools = get_chat_tools(mock_sentinel)
    breaker_tool = next(t for t in tools if t.name == "get_agent_circuit_breakers")
    result = breaker_tool.invoke({"reason": "test"})
    assert "All agents healthy" in result


def test_get_agent_circuit_breakers_active():
    mock_sentinel = MagicMock()
    mock_sentinel.orchestrator.agent_circuit_breakers = {"agent_a": 1, "agent_b": 6}

    with patch.dict(os.environ, {"CIRCUIT_BREAKER_THRESHOLD": "5"}):
        tools = get_chat_tools(mock_sentinel)
        breaker_tool = next(t for t in tools if t.name == "get_agent_circuit_breakers")
        result = breaker_tool.invoke({"reason": "test"})
        assert "Agent: agent_a | Errors: 1/5 | Status: HEALTHY" in result
        assert "Agent: agent_b | Errors: 6/5 | Status: TRIPPED (Blocked)" in result


def test_get_agent_circuit_breakers_failure():
    tools = get_chat_tools(
        None
    )  # Will cause AttributeError when trying to access orchestrator
    breaker_tool = next(t for t in tools if t.name == "get_agent_circuit_breakers")
    result = breaker_tool.invoke({"reason": "test"})
    assert "Error retrieving agent circuit breakers" in result


def test_read_project_readme_success():
    tools = get_chat_tools(None)
    readme_tool = next(t for t in tools if t.name == "read_project_readme")

    with patch(
        "builtins.open",
        MagicMock(
            return_value=MagicMock(
                __enter__=MagicMock(
                    return_value=MagicMock(
                        read=MagicMock(return_value="Readme Content")
                    )
                )
            )
        ),
    ):
        with patch("os.path.exists", return_value=True):
            result = readme_tool.invoke({"reason": "test"})
            assert result == "Readme Content"


def test_read_project_readme_not_found():
    tools = get_chat_tools(None)
    readme_tool = next(t for t in tools if t.name == "read_project_readme")

    with patch("os.path.exists", return_value=False):
        result = readme_tool.invoke({"reason": "test"})
        assert "Error: README.md not found" in result
