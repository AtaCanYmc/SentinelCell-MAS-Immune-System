import pytest
from testcontainers.redis import RedisContainer
from src.core.registry_factory import RedisRegistryStore


@pytest.fixture(scope="module")
def redis_container():
    """
    Spins up a real Redis container for integration tests.
    It automatically cleans up after the module tests finish.
    """
    with RedisContainer("redis:7-alpine") as redis:
        yield redis


@pytest.mark.asyncio
async def test_redis_registry_integration(redis_container, monkeypatch):
    """
    Tests the RedisRegistryStore against a live, isolated Redis container.
    """
    # Testcontainers might map the port to a random high port
    redis_url = f"redis://{redis_container.get_container_host_ip()}:{redis_container.get_exposed_port(6379)}"
    monkeypatch.setenv("REDIS_URL", redis_url)

    store = RedisRegistryStore()

    # Test update
    await store.update_schema("Integration_Agent", '{"property": "test"}')

    # Test get
    schema = await store.get_schema("Integration_Agent")
    assert schema == '{"property": "test"}'

    # Test get non-existent
    missing = await store.get_schema("Ghost_Agent")
    assert missing is None
