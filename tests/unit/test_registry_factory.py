import pytest
from unittest.mock import patch

from src.core.registry_factory import (
    RegistryFactory,
    InMemoryRegistryStore,
    FileRegistryStore,
    RedisRegistryStore,
    SqliteRegistryStore,
    PostgresRegistryStore,
    SupabaseRegistryStore,
    MongoRegistryStore,
    FirebaseRegistryStore,
)


@pytest.mark.asyncio
async def test_in_memory_registry_store():
    store = InMemoryRegistryStore()
    await store.update_schema("Agent1", '{"type": "object"}')
    schema = await store.get_schema("Agent1")
    assert schema == '{"type": "object"}'
    assert await store.get_schema("Unknown") is None


@pytest.mark.asyncio
async def test_file_registry_store(tmp_path, monkeypatch):
    registry_file = tmp_path / "test_registry.json"
    monkeypatch.setenv("SCHEMA_FILE_PATH", str(registry_file))

    store = FileRegistryStore()
    await store.update_schema("AgentFile", '{"id": 1}')
    schema = await store.get_schema("AgentFile")
    assert schema == '{"id": 1}'
    assert await store.get_schema("Ghost") is None


def test_registry_factory_init(monkeypatch):
    monkeypatch.setenv("SCHEMA_REGISTRY_PROVIDER", "IN_MEMORY")
    store = RegistryFactory.get_registry_store()
    assert isinstance(store, InMemoryRegistryStore)

    # Test fallback
    monkeypatch.setenv("SCHEMA_REGISTRY_PROVIDER", "UNKNOWN")
    store = RegistryFactory.get_registry_store()
    assert isinstance(store, InMemoryRegistryStore)


@patch("redis.Redis.from_url")
@patch("sqlite3.connect")
@patch("psycopg2.connect")
@patch("supabase.create_client")
@patch("motor.motor_asyncio.AsyncIOMotorClient")
@patch("firebase_admin.firestore_async.client")
@patch("firebase_admin.initialize_app")
@patch("firebase_admin.credentials.Certificate")
@patch("importlib.util.find_spec")
def test_providers_init(
    mock_find,
    mock_cert,
    mock_init,
    mock_firestore,
    mock_motor,
    mock_supabase,
    mock_psycopg,
    mock_sqlite,
    mock_redis,
    monkeypatch,
):
    mock_find.return_value = True
    monkeypatch.setenv("REDIS_URL", "redis://")
    monkeypatch.setenv("SCHEMA_SQLITE_PATH", "schemas.db")
    monkeypatch.setenv("SCHEMA_POSTGRES_URI", "postgresql://")
    monkeypatch.setenv("SUPABASE_URL", "http://")
    monkeypatch.setenv("SUPABASE_KEY", "key")
    monkeypatch.setenv("MONGO_URI", "mongodb://")
    monkeypatch.setenv("FIREBASE_CREDENTIALS_PATH", "fake.json")

    RedisRegistryStore()
    SqliteRegistryStore()
    PostgresRegistryStore()
    SupabaseRegistryStore()
    MongoRegistryStore()
    FirebaseRegistryStore()
