import pytest
from testcontainers.postgres import PostgresContainer
from src.core.registry_factory import PostgresRegistryStore


@pytest.fixture(scope="module")
def postgres_container():
    """
    Spins up a real PostgreSQL container for integration tests.
    """
    with PostgresContainer("postgres:15-alpine") as postgres:
        yield postgres


@pytest.mark.asyncio
async def test_postgres_registry_integration(postgres_container, monkeypatch):
    """
    Tests the PostgresRegistryStore against a live, isolated Postgres container.
    """
    # sqlalchemy format (postgresql+psycopg2://) returned by testcontainers needs to be converted for pure psycopg2
    db_url = postgres_container.get_connection_url()
    db_url = db_url.replace("postgresql+psycopg2://", "postgresql://")

    monkeypatch.setenv("SCHEMA_POSTGRES_URI", db_url)

    # Store auto-initializes the DB table inside __init__
    store = PostgresRegistryStore()

    # Test inserting new schema
    await store.update_schema("PG_Agent", '{"role": "db_test"}')
    schema = await store.get_schema("PG_Agent")
    assert schema == '{"role": "db_test"}'

    # Test upserting (updating existing)
    await store.update_schema("PG_Agent", '{"role": "db_test_updated"}')
    updated = await store.get_schema("PG_Agent")
    assert updated == '{"role": "db_test_updated"}'

    # Test non-existent
    missing = await store.get_schema("No_Agent")
    assert missing is None
