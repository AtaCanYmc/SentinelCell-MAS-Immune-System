import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.gateways.outbox_worker import process_outbox
import json


@pytest.mark.asyncio
@patch("src.gateways.outbox_worker.redis.from_url")
@patch("src.core.memory_factory.MemoryFactory.get_memory_store")
async def test_process_outbox(mock_memory_factory, mock_redis_from_url):
    mock_redis = AsyncMock()
    mock_redis.rpop.return_value = None
    mock_redis.brpoplpush.side_effect = [
        json.dumps(
            {
                "doc_id": "test_id",
                "memory_doc": "test_doc",
                "metadata": {"test": "meta"},
            }
        ).encode(),
        Exception("Break loop"),
    ]
    mock_redis_from_url.return_value = mock_redis

    mock_memory_store = MagicMock()
    mock_memory_factory.return_value = mock_memory_store

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        mock_sleep.side_effect = Exception("Break loop entirely")
        try:
            await process_outbox()
        except Exception:
            pass

    mock_memory_store.add_memory.assert_called_once_with(
        doc_id="test_id", memory_doc="test_doc", metadata={"test": "meta"}
    )
