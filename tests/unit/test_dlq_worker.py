import pytest
import json
from unittest.mock import patch, AsyncMock
from src.gateways.dlq_worker import process_dlq


@pytest.fixture
def mock_dependencies():
    with patch(
        "src.gateways.dlq_worker.BrokerFactory.get_broker"
    ) as mock_get_broker, patch("src.gateways.dlq_worker.asyncio.sleep") as mock_sleep:
        mock_broker_instance = AsyncMock()
        mock_get_broker.return_value = mock_broker_instance
        mock_sleep.side_effect = Exception("stop_loop")
        yield mock_broker_instance


@pytest.mark.asyncio
async def test_process_dlq_success(mock_dependencies):
    mock_broker = mock_dependencies

    # Simulate message from DLQ
    test_msg = json.dumps(
        {
            "source": "A",
            "target": "B",
            "payload": '{"test":"payload"}',
            "dlq_retry_count": 0,
        }
    )

    mock_broker.pop_atomic.side_effect = [
        (test_msg.encode("utf-8"), "mock_ack"),
        Exception("broker error"),
    ]

    try:
        await process_dlq()
    except Exception as e:
        if str(e) != "stop_loop":
            raise

    # Should push to main bus
    mock_broker.push.assert_called_once()
    assert mock_broker.push.call_args[0][0] == "sentinel.in"
    # Should ack
    mock_broker.acknowledge.assert_called_once()


@pytest.mark.asyncio
async def test_process_dlq_drop_max_retries(mock_dependencies):
    mock_broker = mock_dependencies

    # Simulate message with max retries
    test_msg = json.dumps(
        {
            "source": "A",
            "target": "B",
            "payload": '{"test":"payload"}',
            "dlq_retry_count": 3,
        }
    )

    mock_broker.pop_atomic.side_effect = [
        (test_msg.encode("utf-8"), "mock_ack"),
        Exception("broker error"),
    ]

    try:
        await process_dlq()
    except Exception as e:
        if str(e) != "stop_loop":
            raise

    # Should NOT push to main bus
    mock_broker.push.assert_not_called()
    # Should ack to clear from processing
    mock_broker.acknowledge.assert_called_once()
