import pytest
from src.core.memory_factory import MemoryFactory, InMemoryMemoryStore


def test_memory_factory_in_memory():
    store = MemoryFactory.get_memory_store("IN_MEMORY")
    assert isinstance(store, InMemoryMemoryStore)

    # Test interface
    store.add_memory("doc1", "test memory", {"schema": "Test"})
    assert store.query_memory("test") == "test memory"

    store.delete_memory("doc1")
    assert store.query_memory("test") is None


def test_memory_factory_invalid_provider():
    with pytest.raises(ValueError):
        MemoryFactory.get_memory_store("INVALID_DB")
