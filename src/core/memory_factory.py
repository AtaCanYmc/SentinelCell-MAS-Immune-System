import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

try:
    import chromadb

    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


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
        elif provider == "IN_MEMORY":
            return InMemoryMemoryStore()
        else:
            raise ValueError(f"Unsupported Vector Database provider: {provider}")
