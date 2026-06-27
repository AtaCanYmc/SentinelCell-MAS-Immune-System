import time
from unittest.mock import patch
from fastapi.testclient import TestClient
from src.core.memory_factory import InMemoryMemoryStore
from src.gateways.fastapi_gateway import app


def test_in_memory_purge():
    store = InMemoryMemoryStore()

    # Add a memory from 40 days ago
    old_timestamp = time.time() - (40 * 86400)
    store.add_memory("doc1", "old memory", {"timestamp": old_timestamp})

    # Add a memory from today
    store.add_memory("doc2", "new memory", {"timestamp": time.time()})

    # Purge memories older than 30 days
    deleted_count = store.purge_old_memories(days=30)

    assert deleted_count == 1
    assert "doc1" not in store.storage
    assert "doc2" in store.storage


def test_purge_endpoint_success(monkeypatch):
    monkeypatch.setenv("API_KEY_SECRET", "test-key")

    with patch(
        "src.core.memory_factory.MemoryFactory.get_memory_store"
    ) as mock_get_store:
        mock_store = mock_get_store.return_value
        mock_store.purge_old_memories.return_value = 5

        client = TestClient(app)
        response = client.delete(
            "/memory/purge?days=30", headers={"Authorization": "Bearer test-key"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "deleted_count" in data
    assert data["deleted_count"] == 5
