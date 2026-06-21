import pytest
import asyncio
import json
from unittest.mock import patch, AsyncMock, MagicMock
from src.gateways.redis_mq import mq_worker


@pytest.fixture
def mock_dependencies():
    with patch("src.gateways.redis_mq.redis.from_url") as mock_redis, patch(
        "src.gateways.redis_mq.SentinelCell"
    ) as MockSentinel, patch("src.gateways.redis_mq.asyncio.sleep") as mock_sleep:
        mock_redis_instance = AsyncMock()
        mock_redis.return_value = mock_redis_instance

        mock_sentinel_instance = MagicMock()
        mock_sentinel_instance.intercept = AsyncMock()
        MockSentinel.return_value = mock_sentinel_instance

        # We need to simulate sleep throwing CancelledError to break the infinite while loop
        mock_sleep.side_effect = asyncio.CancelledError()

        yield mock_redis_instance, mock_sentinel_instance


@pytest.mark.asyncio
async def test_mq_worker_process_success(mock_dependencies):
    mock_redis, mock_sentinel = mock_dependencies

    # Simulate intercept success
    mock_sentinel.intercept.return_value = {"status": "success", "data": "clean"}

    # Simulate a single message popping from the queue
    test_msg = json.dumps({"source": "A", "target": "B", "payload": '{"broken":"yes"}'})

    # blpop returns a tuple (queue_name, data)
    # Then we return None to let the loop hit the exception and sleep (which raises CancelledError)
    mock_redis.blpop.side_effect = [
        (b"sentinel.in", test_msg.encode("utf-8")),
        Exception("stop"),
    ]

    try:
        await mq_worker()
    except asyncio.CancelledError:
        pass

    # It should have published to sentinel.out
    mock_redis.rpush.assert_called_once_with(
        "sentinel.out", json.dumps({"status": "success", "data": "clean"})
    )


@pytest.mark.asyncio
async def test_mq_worker_process_drop(mock_dependencies):
    mock_redis, mock_sentinel = mock_dependencies

    # Simulate intercept returning None (quarantine/malicious drop)
    mock_sentinel.intercept.return_value = None

    test_msg = json.dumps({"source": "A", "target": "B", "payload": '{"evil":"yes"}'})
    mock_redis.blpop.side_effect = [
        (b"sentinel.in", test_msg.encode("utf-8")),
        Exception("stop"),
    ]

    try:
        await mq_worker()
    except asyncio.CancelledError:
        pass

    # It should NOT publish anything
    mock_redis.rpush.assert_not_called()
