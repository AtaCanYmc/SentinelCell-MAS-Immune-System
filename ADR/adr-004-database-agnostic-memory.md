# ADR 004: Database Agnostic Memory (VectorDBFactory)

## Status
**Accepted**

## Context
SentinelCell relies on a Retrieval-Augmented Generation (RAG) system to maintain long-term memory of its self-healing processes (Adaptive RAG). Initially, this system was heavily coupled with ChromaDB. While ChromaDB is excellent for local rapid development, enterprise deployments often demand scalable, centralized, and cloud-native solutions like PostgreSQL (PGVector) or Pinecone. Hardcoding a single database restricted the agent's deployment flexibility and created a single point of failure.

## Decision
We decided to decouple the vector database engine from the core agent logic by implementing a "Database Agnostic" architecture using the Factory Design Pattern (`MemoryFactory`).

1. **`BaseMemoryStore` Interface**: We established a strict contract with `add_memory`, `query_memory`, and `delete_memory` methods.
2. **Multiple Connectors**:
   - `ChromaMemoryStore`: For zero-configuration local usage.
   - `PGVectorMemoryStore`: For enterprise-grade SQL-based vector persistence (requires `pgvector`).
   - `PineconeMemoryStore`: For fully managed cloud vector search.
   - `InMemoryMemoryStore`: For fast, dependency-free testing and CI/CD pipelines.
3. **Environment-Driven Injection**: The active database is chosen dynamically at runtime via the `VECTOR_DB_PROVIDER` environment variable.
4. **Decoupled Embeddings**: For databases that do not generate their own embeddings natively (like Postgres and Pinecone), we standardize on using `langchain_openai.OpenAIEmbeddings` to handle vectorization before insertion.

## Consequences

### Positive
- **Flexibility**: Users can switch between local, SQL, and Cloud vector databases simply by changing an environment variable, without altering the core logic.
- **Enterprise Readiness**: Support for PGVector and Pinecone significantly boosts the appeal of SentinelCell for large-scale production deployments.
- **Testability**: The `InMemoryMemoryStore` allows the entire RAG test suite to run in milliseconds without requiring external Docker containers or file I/O operations.

### Negative
- **Embedding Dependency**: PGVector and Pinecone implementations introduced a minor dependency on OpenAI (`langchain_openai`) to handle vectorization, meaning those specific providers require an API key to function.
- **Complexity**: Multiple connectors require maintaining distinct integration setups (e.g., `docker-compose.postgres.yml`).
