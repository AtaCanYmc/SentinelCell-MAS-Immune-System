import pytest
import asyncio
import json
from unittest.mock import patch, AsyncMock, MagicMock
from src.gateways.ingress_mq import mq_worker


@pytest.fixture
def mock_dependencies():
    with patch(
        "src.gateways.ingress_mq.BrokerFactory.get_broker"
    ) as mock_get_broker, patch(
        "src.gateways.ingress_mq.SentinelCell"
    ) as MockSentinel, patch("src.gateways.ingress_mq.asyncio.sleep") as mock_sleep:
        mock_broker_instance = AsyncMock()
        mock_get_broker.return_value = mock_broker_instance

        mock_sentinel_instance = MagicMock()
        mock_sentinel_instance.intercept = AsyncMock()
        MockSentinel.return_value = mock_sentinel_instance

        mock_sleep.side_effect = asyncio.CancelledError()

        yield mock_broker_instance, mock_sentinel_instance


@pytest.mark.asyncio
async def test_mq_worker_process_success(mock_dependencies):
    mock_broker, mock_sentinel = mock_dependencies

    # Simulate intercept success
    mock_sentinel.intercept.return_value = {"status": "success", "data": "clean"}

    test_msg = json.dumps({"source": "A", "target": "B", "payload": '{"broken":"yes"}'})

    mock_broker.consume.side_effect = [
        test_msg,
        Exception("stop"),
    ]

    try:
        await mq_worker()
    except asyncio.CancelledError:
        pass
    except Exception as e:
        if str(e) != "stop":
            raise

    # It should have published to sentinel.out
    mock_broker.push.assert_called_once()
    args, kwargs = mock_broker.push.call_args
    assert args[0] == "sentinel.out"


@pytest.mark.asyncio
async def test_mq_worker_process_drop(mock_dependencies):
    mock_broker, mock_sentinel = mock_dependencies

    mock_sentinel.intercept.return_value = None

    test_msg = json.dumps({"source": "A", "target": "B", "payload": '{"evil":"yes"}'})
    mock_broker.consume.side_effect = [
        test_msg,
        Exception("stop"),
    ]

    try:
        await mq_worker()
    except asyncio.CancelledError:
        pass
    except Exception as e:
        if str(e) != "stop":
            raise

    mock_broker.push.assert_not_called()
