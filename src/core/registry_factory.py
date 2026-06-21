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


class SupabaseRegistryStore(BaseRegistryStore):
    """
    Supabase (PostgreSQL) backed Schema Registry.
    """

    def __init__(self):
        try:
            from supabase import create_client
        except ImportError:
            raise ImportError("Please install 'supabase' to use SupabaseRegistryStore")

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")

        self.client = create_client(url, key)

    async def get_schema(self, agent_id: str) -> Optional[str]:
        try:
            import asyncio

            response = await asyncio.to_thread(
                self.client.table("schemas")
                .select("schema_json")
                .eq("agent_id", agent_id)
                .execute
            )
            if response.data and len(response.data) > 0:
                return response.data[0].get("schema_json")
            return None
        except Exception as e:
            logger.error(f"Supabase get_schema error: {e}")
            return None

    async def update_schema(self, agent_id: str, schema_json: str) -> None:
        try:
            import asyncio

            data = {"agent_id": agent_id, "schema_json": schema_json}
            await asyncio.to_thread(self.client.table("schemas").upsert(data).execute)
        except Exception as e:
            logger.error(f"Supabase update_schema error: {e}")
            raise


class MongoRegistryStore(BaseRegistryStore):
    """
    MongoDB (NoSQL) backed Schema Registry using Motor (async).
    """

    def __init__(self):
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
        except ImportError:
            raise ImportError("Please install 'motor' to use MongoRegistryStore")

        uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client.get_database("sentinel")
        self.collection = self.db.get_collection("schemas")

    async def get_schema(self, agent_id: str) -> Optional[str]:
        try:
            doc = await self.collection.find_one({"agent_id": agent_id})
            if doc:
                return doc.get("schema_json")
            return None
        except Exception as e:
            logger.error(f"Mongo get_schema error: {e}")
            return None

    async def update_schema(self, agent_id: str, schema_json: str) -> None:
        try:
            await self.collection.update_one(
                {"agent_id": agent_id},
                {"$set": {"schema_json": schema_json}},
                upsert=True,
            )
        except Exception as e:
            logger.error(f"Mongo update_schema error: {e}")
            raise


class FirebaseRegistryStore(BaseRegistryStore):
    """
    Firebase (Firestore) backed Schema Registry using firebase-admin async client.
    """

    def __init__(self):
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore_async
        except ImportError:
            raise ImportError(
                "Please install 'firebase-admin' to use FirebaseRegistryStore"
            )

        if not firebase_admin._apps:
            cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
            if cred_path:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            else:
                firebase_admin.initialize_app()

        self.db = firestore_async.client()

    async def get_schema(self, agent_id: str) -> Optional[str]:
        try:
            doc_ref = self.db.collection("schemas").document(agent_id)
            doc = await doc_ref.get()
            if doc.exists:
                return doc.to_dict().get("schema_json")
            return None
        except Exception as e:
            logger.error(f"Firebase get_schema error: {e}")
            return None

    async def update_schema(self, agent_id: str, schema_json: str) -> None:
        try:
            doc_ref = self.db.collection("schemas").document(agent_id)
            await doc_ref.set({"schema_json": schema_json})
        except Exception as e:
            logger.error(f"Firebase update_schema error: {e}")
            raise


class SqliteRegistryStore(BaseRegistryStore):
    """
    SQLite backed local relational Schema Registry.
    Built-in to Python, requires no external dependencies.
    """

    def __init__(self):
        self.db_path = os.getenv("SQLITE_DB_PATH", "schemas.db")
        self._init_db()

    def _init_db(self):
        import sqlite3

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schemas (
                    agent_id TEXT PRIMARY KEY,
                    schema_json TEXT NOT NULL
                )
            """)
            conn.commit()

    async def get_schema(self, agent_id: str) -> Optional[str]:
        try:
            import sqlite3
            import asyncio

            def _fetch():
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT schema_json FROM schemas WHERE agent_id = ?",
                        (agent_id,),
                    )
                    row = cursor.fetchone()
                    return row[0] if row else None

            return await asyncio.to_thread(_fetch)
        except Exception as e:
            logger.error(f"SQLite get_schema error: {e}")
            return None

    async def update_schema(self, agent_id: str, schema_json: str) -> None:
        try:
            import sqlite3
            import asyncio

            def _update():
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO schemas (agent_id, schema_json)
                        VALUES (?, ?)
                        ON CONFLICT(agent_id)
                        DO UPDATE SET schema_json=excluded.schema_json
                    """,
                        (agent_id, schema_json),
                    )
                    conn.commit()

            await asyncio.to_thread(_update)
        except Exception as e:
            logger.error(f"SQLite update_schema error: {e}")
            raise


class PostgresRegistryStore(BaseRegistryStore):
    """
    Local PostgreSQL backed Schema Registry using psycopg2.
    """

    def __init__(self):
        import importlib.util

        if importlib.util.find_spec("psycopg2") is None:
            raise ImportError(
                "Please install 'psycopg2-binary' to use PostgresRegistryStore"
            )

        self.uri = os.getenv("SCHEMA_POSTGRES_URI") or os.getenv("POSTGRES_URI")
        if not self.uri:
            raise ValueError("SCHEMA_POSTGRES_URI or POSTGRES_URI must be set in .env")

        self._init_db()

    def _init_db(self):
        import psycopg2

        try:
            with psycopg2.connect(self.uri) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS mcp_schemas (
                            agent_id VARCHAR(255) PRIMARY KEY,
                            schema_json TEXT NOT NULL
                        )
                    """)
                conn.commit()
        except Exception as e:
            logger.error(f"Postgres _init_db error: {e}")

    async def get_schema(self, agent_id: str) -> Optional[str]:
        try:
            import psycopg2
            import asyncio

            def _fetch():
                with psycopg2.connect(self.uri) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "SELECT schema_json FROM mcp_schemas WHERE agent_id = %s",
                            (agent_id,),
                        )
                        row = cursor.fetchone()
                        return row[0] if row else None

            return await asyncio.to_thread(_fetch)
        except Exception as e:
            logger.error(f"Postgres get_schema error: {e}")
            return None

    async def update_schema(self, agent_id: str, schema_json: str) -> None:
        try:
            import psycopg2
            import asyncio

            def _update():
                with psycopg2.connect(self.uri) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO mcp_schemas (agent_id, schema_json)
                            VALUES (%s, %s)
                            ON CONFLICT (agent_id)
                            DO UPDATE SET schema_json = EXCLUDED.schema_json
                        """,
                            (agent_id, schema_json),
                        )
                    conn.commit()

            await asyncio.to_thread(_update)
        except Exception as e:
            logger.error(f"Postgres update_schema error: {e}")
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
        elif provider == "SUPABASE":
            logger.info("Initializing Schema Registry: SUPABASE")
            return SupabaseRegistryStore()
        elif provider == "MONGO":
            logger.info("Initializing Schema Registry: MONGO")
            return MongoRegistryStore()
        elif provider == "FIREBASE":
            logger.info("Initializing Schema Registry: FIREBASE")
            return FirebaseRegistryStore()
        elif provider == "SQLITE":
            logger.info("Initializing Schema Registry: SQLITE")
            return SqliteRegistryStore()
        elif provider == "POSTGRES":
            logger.info("Initializing Schema Registry: POSTGRES")
            return PostgresRegistryStore()
        else:
            logger.warning(
                f"Unknown registry provider {provider}, falling back to IN_MEMORY"
            )
            return InMemoryRegistryStore()


# Global Singleton for the Registry Store
registry_store = RegistryFactory.get_registry_store()
