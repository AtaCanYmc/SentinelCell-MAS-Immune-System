import pytest
from unittest.mock import patch
from src.core.memory_factory import (
    MemoryFactory,
    InMemoryMemoryStore,
    ChromaMemoryStore,
    PGVectorMemoryStore,
    PineconeMemoryStore,
)


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


@patch("chromadb.PersistentClient")
@patch("psycopg2.connect")
@patch("src.core.memory_factory.Pinecone")
@patch("importlib.util.find_spec")
@patch("src.core.memory_factory.register_vector", create=True)
def test_memory_providers_init(
    mock_register, mock_find_spec, mock_pinecone, mock_psycopg, mock_chroma, monkeypatch
):
    mock_find_spec.return_value = True
    monkeypatch.setenv("CHROMA_DB_DIR", "./fake_chroma")
    monkeypatch.setenv("MEMORY_POSTGRES_URI", "postgresql://fake")
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    monkeypatch.setenv("PINECONE_API_KEY", "fake")

    ChromaMemoryStore()
    PGVectorMemoryStore()
    PineconeMemoryStore()
