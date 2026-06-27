import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.gateways.outbox_worker import process_outbox
import json


@pytest.mark.asyncio
@patch("src.gateways.outbox_worker.BrokerFactory.get_broker")
@patch("src.core.memory_factory.MemoryFactory.get_memory_store")
async def test_process_outbox(mock_memory_store_factory, mock_get_broker):
    mock_broker = AsyncMock()
    mock_get_broker.return_value = mock_broker

    mock_broker.pop_atomic.side_effect = [
        None,  # For startup recovery loop
        json.dumps(
            {
                "doc_id": "test_id",
                "memory_doc": "test_doc",
                "metadata": {"test": "meta"},
            }
        ).encode(),
        Exception("Break loop"),
    ]

    mock_memory_store = MagicMock()
    mock_memory_store_factory.return_value = mock_memory_store

    with patch(
        "src.gateways.outbox_worker.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        mock_sleep.side_effect = Exception("stop_loop")
        try:
            await process_outbox()
        except Exception as e:
            if str(e) != "stop_loop":
                raise

    mock_memory_store.add_memory.assert_called_once_with(
        doc_id="test_id", memory_doc="test_doc", metadata={"test": "meta"}
    )
    mock_broker.acknowledge.assert_called_once()
