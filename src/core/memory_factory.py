import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

try:
    import chromadb

    CHROMA_AVAILABLE = True
except ImportError:
    chromadb = None
    CHROMA_AVAILABLE = False

try:
    import psycopg2
    from pgvector.psycopg2 import register_vector
    from langchain_openai import OpenAIEmbeddings
    import json

    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False

try:
    from pinecone import Pinecone

    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False


class BaseMemoryStore(ABC):
    """
    Abstract Interface for Vector Databases / Memory Stores.
    Ensures that SentinelCell can switch databases (Chroma, Pinecone, PGVector, etc.) seamlessly.
    """

    @abstractmethod
    def add_memory(self, doc_id: str, memory_doc: str, metadata: dict) -> None:
        pass

    @abstractmethod
    def query_memory(self, query_str: str, n_results: int = 1) -> Optional[str]:
        pass

    @abstractmethod
    def delete_memory(self, doc_id: str) -> None:
        pass

    @abstractmethod
    def purge_old_memories(self, days: int) -> int:
        pass


class ChromaMemoryStore(BaseMemoryStore):
    """
    ChromaDB implementation of the Memory Store.
    """

    def __init__(self):
        if not CHROMA_AVAILABLE:
            raise ImportError("chromadb is not installed. Run: pip install chromadb")
        db_path = os.path.join(os.getcwd(), "chroma_db")
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name="healing_memory")

    def add_memory(self, doc_id: str, memory_doc: str, metadata: dict) -> None:
        self.collection.add(
            documents=[memory_doc],
            metadatas=[metadata],
            ids=[doc_id],
        )

    def query_memory(self, query_str: str, n_results: int = 1) -> Optional[str]:
        results = self.collection.query(query_texts=[query_str], n_results=n_results)
        if results.get("documents") and results["documents"][0]:
            return results["documents"][0][0]
        return None

    def delete_memory(self, doc_id: str) -> None:
        self.collection.delete(ids=[doc_id])

    def purge_old_memories(self, days: int) -> int:
        import time

        threshold = time.time() - (days * 86400)
        try:
            # ChromaDB supports where filters on metadata
            # We will fetch ids matching the filter and delete them to count them
            results = self.collection.get(where={"timestamp": {"$lt": threshold}})
            ids_to_delete = results.get("ids", [])
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
            return len(ids_to_delete)
        except Exception:
            return 0


class InMemoryMemoryStore(BaseMemoryStore):
    """
    A lightweight, Python dict-based memory store.
    Useful for testing or environments where a persistent VectorDB is not possible.
    Note: Does not perform semantic search, relies on exact/substring matches for simplicity.
    """

    def __init__(self):
        self.storage: Dict[str, Dict[str, Any]] = {}

    def add_memory(self, doc_id: str, memory_doc: str, metadata: dict) -> None:
        self.storage[doc_id] = {"document": memory_doc, "metadata": metadata}

    def query_memory(self, query_str: str, n_results: int = 1) -> Optional[str]:
        # A rudimentary fallback "search" mimicking vector search logic
        # (Very basic substring matching for the sake of the mock)
        best_match = None
        for doc_id, data in self.storage.items():
            if query_str.split("Error: ")[-1].split(" Schema:")[0] in data["document"]:
                best_match = data["document"]
                break

        # If no strict match, just return the first one (or none)
        if not best_match and self.storage:
            best_match = list(self.storage.values())[0]["document"]

        return best_match

    def delete_memory(self, doc_id: str) -> None:
        if doc_id in self.storage:
            del self.storage[doc_id]

    def purge_old_memories(self, days: int) -> int:
        import time

        threshold = time.time() - (days * 86400)
        to_delete = []
        for doc_id, data in self.storage.items():
            metadata = data.get("metadata", {})
            timestamp = metadata.get("timestamp")
            if timestamp is not None and timestamp < threshold:
                to_delete.append(doc_id)

        for doc_id in to_delete:
            del self.storage[doc_id]

        return len(to_delete)


class PGVectorMemoryStore(BaseMemoryStore):
    """
    PostgreSQL (PGVector) implementation of the Memory Store.
    Uses OpenAIEmbeddings to convert text to vectors before inserting/querying.
    """

    def __init__(self):
        if not PGVECTOR_AVAILABLE:
            raise ImportError(
                "psycopg2, pgvector, or langchain_openai is not installed."
            )

        self.uri = os.getenv("POSTGRES_URI")
        if not self.uri:
            raise ValueError("POSTGRES_URI is not set in the environment.")

        self.embeddings = OpenAIEmbeddings()
        self.conn = psycopg2.connect(self.uri)
        register_vector(self.conn)
        self._init_db()

    def _init_db(self):
        with self.conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS healing_memory (
                    id VARCHAR(255) PRIMARY KEY,
                    memory_doc TEXT,
                    metadata JSONB,
                    embedding vector(1536)
                )
            """)
            self.conn.commit()

    def add_memory(self, doc_id: str, memory_doc: str, metadata: dict) -> None:
        vector = self.embeddings.embed_query(memory_doc)
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO healing_memory (id, memory_doc, metadata, embedding) VALUES (%s, %s, %s, %s)",
                (doc_id, memory_doc, json.dumps(metadata), vector),
            )
            self.conn.commit()

    def query_memory(self, query_str: str, n_results: int = 1) -> Optional[str]:
        vector = self.embeddings.embed_query(query_str)
        with self.conn.cursor() as cur:
            # <=> is cosine distance in pgvector
            cur.execute(
                "SELECT memory_doc FROM healing_memory ORDER BY embedding <=> %s LIMIT %s",
                (vector, n_results),
            )
            result = cur.fetchone()
            if result:
                return result[0]
        return None

    def delete_memory(self, doc_id: str) -> None:
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM healing_memory WHERE id = %s", (doc_id,))
            self.conn.commit()

    def purge_old_memories(self, days: int) -> int:
        import time

        threshold = time.time() - (days * 86400)
        with self.conn.cursor() as cur:
            cur.execute(
                "DELETE FROM healing_memory WHERE (metadata->>'timestamp')::float < %s",
                (threshold,),
            )
            deleted_count = cur.rowcount
            self.conn.commit()
            return deleted_count


class PineconeMemoryStore(BaseMemoryStore):
    """
    Pinecone cloud vector database implementation of the Memory Store.
    Uses OpenAIEmbeddings to convert text to vectors.
    """

    def __init__(self):
        if not PINECONE_AVAILABLE:
            raise ImportError("pinecone is not installed.")

        api_key = os.getenv("PINECONE_API_KEY")
        index_name = os.getenv("PINECONE_INDEX_NAME", "sentinel-healing-memory")

        if not api_key:
            raise ValueError("PINECONE_API_KEY is not set in the environment.")

        self.embeddings = OpenAIEmbeddings()
        self.pc = Pinecone(api_key=api_key)
        self.index = self.pc.Index(index_name)

    def add_memory(self, doc_id: str, memory_doc: str, metadata: dict) -> None:
        vector = self.embeddings.embed_query(memory_doc)
        # Store memory_doc within the metadata so we can retrieve it
        metadata["memory_doc"] = memory_doc
        self.index.upsert(
            vectors=[{"id": doc_id, "values": vector, "metadata": metadata}]
        )

    def query_memory(self, query_str: str, n_results: int = 1) -> Optional[str]:
        vector = self.embeddings.embed_query(query_str)
        response = self.index.query(
            vector=vector, top_k=n_results, include_metadata=True
        )
        if response.matches and len(response.matches) > 0:
            match = response.matches[0]
            if match.metadata and "memory_doc" in match.metadata:
                return match.metadata["memory_doc"]
        return None

    def delete_memory(self, doc_id: str) -> None:
        self.index.delete(ids=[doc_id])

    def purge_old_memories(self, days: int) -> int:
        import time

        threshold = time.time() - (days * 86400)
        try:
            # Pinecone supports deletion by metadata filter
            self.index.delete(filter={"timestamp": {"$lt": threshold}})
            # We don't get a direct count easily, so we return a symbolic 1 or 0
            return 1
        except Exception:
            return 0


class MemoryFactory:
    """
    Database Agnostic Factory.
    Creates BaseMemoryStore instances based on the VECTOR_DB_PROVIDER configuration.
    """

    @staticmethod
    def get_memory_store(provider: Optional[str] = None) -> BaseMemoryStore:
        if not provider:
            provider = os.getenv("VECTOR_DB_PROVIDER", "CHROMADB").upper()

        if provider == "CHROMADB":
            return ChromaMemoryStore()
        elif provider == "PGVECTOR":
            return PGVectorMemoryStore()
        elif provider == "PINECONE":
            return PineconeMemoryStore()
        elif provider == "IN_MEMORY":
            from src.core.logger import get_console

            get_console().print(
                "[bold red][!] WARNING: Using InMemoryMemoryStore mock. "
                "This does not perform true semantic search. "
                "Not for production use![/bold red]"
            )
            return InMemoryMemoryStore()
        else:
            raise ValueError(f"Unsupported Vector Database provider: {provider}")
