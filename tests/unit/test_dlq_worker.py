import pytest
from unittest.mock import patch, AsyncMock, mock_open
from src.gateways.dlq_worker import process_dlq
import json


@pytest.mark.asyncio
@patch("src.gateways.dlq_worker.redis.from_url")
async def test_process_dlq(mock_redis_from_url):
    mock_redis = AsyncMock()
    mock_redis_from_url.return_value = mock_redis

    mock_file_content = (
        json.dumps(
            {
                "timestamp": 12345,
                "source": "A",
                "target": "B",
                "payload": '{"test":"payload"}',
            }
        )
        + "\n"
    )

    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        with patch("os.path.exists", return_value=True):
            with patch("os.rename"):
                with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                    mock_sleep.side_effect = Exception("Break loop")
                    try:
                        await process_dlq()
                    except Exception:
                        pass

    mock_redis.lpush.assert_called_once()
