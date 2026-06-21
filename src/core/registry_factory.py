import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class BaseRegistryStore(ABC):
    """
    Abstract Base Class for Schema Registry Stores.
    Provides agnostic interface to retrieve and update JSON Schemas.
    """

    @abstractmethod
    async def get_schema(self, agent_id: str) -> Optional[str]:
        pass

    @abstractmethod
    async def update_schema(self, agent_id: str, schema_json: str) -> None:
        pass


class InMemoryRegistryStore(BaseRegistryStore):
    """
    Lightweight Memory Store for testing and rapid local development.
    """

    def __init__(self):
        self._registry = {}

    async def get_schema(self, agent_id: str) -> Optional[str]:
        return self._registry.get(agent_id)

    async def update_schema(self, agent_id: str, schema_json: str) -> None:
        self._registry[agent_id] = schema_json


class FileRegistryStore(BaseRegistryStore):
    """
    Persistent Local File Store for schemas.
    Stores schemas in a single JSON file.
    """

    def __init__(self, file_path: str = "schemas.json"):
        self.file_path = file_path
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump({}, f)

    def _read_data(self) -> dict:
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _write_data(self, data: dict) -> None:
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=2)

    async def get_schema(self, agent_id: str) -> Optional[str]:
        data = self._read_data()
        return data.get(agent_id)

    async def update_schema(self, agent_id: str, schema_json: str) -> None:
        data = self._read_data()
        data[agent_id] = schema_json
        self._write_data(data)


class RedisRegistryStore(BaseRegistryStore):
    """
    Distributed, Enterprise-Ready Store backed by Redis.
    Guarantees strong consistency across multi-node setups.
    """

    def __init__(self):
        # We import redis lazily so it's only required if this provider is chosen
        import redis.asyncio as redis

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.client = redis.from_url(redis_url)

    async def get_schema(self, agent_id: str) -> Optional[str]:
        try:
            schema = await self.client.get(f"schema:{agent_id}")
            if schema:
                return schema.decode("utf-8")
            return None
        except Exception as e:
            logger.error(f"Redis get_schema error: {e}")
            return None

    async def update_schema(self, agent_id: str, schema_json: str) -> None:
        try:
            await self.client.set(f"schema:{agent_id}", schema_json)
        except Exception as e:
            logger.error(f"Redis update_schema error: {e}")
            raise


class RegistryFactory:
    """
    Factory to instantiate the appropriate Registry Store based on environment variables.
    """

    @staticmethod
    def get_registry_store() -> BaseRegistryStore:
        provider = os.getenv("SCHEMA_REGISTRY_PROVIDER", "REDIS").upper()

        if provider == "IN_MEMORY":
            logger.info("Initializing Schema Registry: IN_MEMORY")
            return InMemoryRegistryStore()
        elif provider == "FILE":
            logger.info("Initializing Schema Registry: FILE")
            return FileRegistryStore()
        elif provider == "REDIS":
            logger.info("Initializing Schema Registry: REDIS")
            return RedisRegistryStore()
        else:
            logger.warning(
                f"Unknown registry provider {provider}, falling back to IN_MEMORY"
            )
            return InMemoryRegistryStore()


# Global Singleton for the Registry Store
registry_store = RegistryFactory.get_registry_store()
