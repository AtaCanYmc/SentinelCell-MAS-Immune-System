import pytest
from unittest.mock import AsyncMock, patch
import time
from src.agents.validator_agent import SentinelCell


@pytest.fixture
def mock_dependencies():
    with (
        patch("src.agents.validator_agent.SchemaRegistryClient") as _,
        patch("src.agents.validator_agent.SemanticValidator") as _,
        patch("src.agents.validator_agent.SelfHealingEngine") as _,
        patch("src.agents.validator_agent.SentinelOrchestrator") as MockOrchestrator,
        patch("src.agents.validator_agent.broadcaster") as mock_broadcaster,
    ):
        mock_orchestrator_instance = AsyncMock()
        MockOrchestrator.return_value = mock_orchestrator_instance

        mock_broadcaster.broadcast = AsyncMock()

        yield mock_orchestrator_instance, mock_broadcaster


@pytest.mark.asyncio
async def test_intercept_successful(mock_dependencies):
    mock_orchestrator, mock_broadcaster = mock_dependencies
    mock_orchestrator.intercept.return_value = {"status": "ok"}

    cell = SentinelCell()

    result = await cell.intercept("SourceAgent", "TargetAgent", '{"data": "test"}')

    assert result == {"status": "ok"}
    mock_broadcaster.broadcast.assert_any_call(
        "INTERCEPT", "Source: SourceAgent -> Target: TargetAgent"
    )
    assert not cell.quarantine_mode
    assert len(cell.error_timestamps) == 0


@pytest.mark.asyncio
async def test_quarantine_mode_activation(mock_dependencies):
    mock_orchestrator, mock_broadcaster = mock_dependencies
    mock_orchestrator.intercept.return_value = None  # Simulate a failure

    cell = SentinelCell()

    # Send 5 failed packets
    for i in range(5):
        result = await cell.intercept("Alpha", "Beta", '{"bad": "data"}')
        assert result is None

    assert cell.quarantine_mode is True
    assert len(cell.error_timestamps) == 5

    # 6th packet should be blocked due to quarantine
    mock_broadcaster.broadcast.reset_mock()
    result_6 = await cell.intercept("Alpha", "Beta", '{"good": "data"}')
    assert result_6 is None
    mock_broadcaster.broadcast.assert_called_with(
        "SECURITY_ALERT", "QUARANTINE BLOCKED TRAFFIC"
    )


@pytest.mark.asyncio
async def test_quarantine_sliding_window(mock_dependencies):
    mock_orchestrator, mock_broadcaster = mock_dependencies
    mock_orchestrator.intercept.return_value = None

    cell = SentinelCell()

    # Simulate 4 errors 65 seconds ago
    old_time = time.time() - 65
    cell.error_timestamps = [old_time] * 4

    # The 5th error comes in now. It should prune the old errors and NOT trigger quarantine.
    result = await cell.intercept("Alpha", "Beta", '{"bad": "data"}')
    assert result is None

    assert cell.quarantine_mode is False
    assert len(cell.error_timestamps) == 1
