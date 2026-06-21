import time
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
    # Mock MemoryFactory to return an InMemoryMemoryStore that we control

    # Force IN_MEMORY provider
    monkeypatch.setenv("VECTOR_DB_PROVIDER", "IN_MEMORY")

    client = TestClient(app)
    response = client.delete("/memory/purge?days=30")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "deleted_count" in data
