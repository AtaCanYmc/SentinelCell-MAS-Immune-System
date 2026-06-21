<div align="center">
  <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/solid/database.svg" width="100" height="100" alt="Database Setup" style="border-radius: 50%;">

  # SentinelCell: Database Agnostic Memory
</div>

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Pinecone](https://img.shields.io/badge/Pinecone-000000?style=for-the-badge&logo=pinecone&logoColor=white)
![ChromaDB](https://img.shields.io/badge/Chroma_DB-FF8000?style=for-the-badge)

</div>

SentinelCell uses an **Adaptive RAG** (Retrieval-Augmented Generation) mechanism to store and recall past LLM repair operations. To maximize enterprise readiness, SentinelCell is strictly **Database Agnostic**. It utilizes a Factory Pattern (`MemoryFactory`) allowing developers to swap Vector Databases without changing core agent logic.

## Supported Providers

You can switch the active provider by setting the `VECTOR_DB_PROVIDER` environment variable in your `.env` file.

| Provider | Configuration Key | Description |
| :--- | :--- | :--- |
| **ChromaDB** | `CHROMADB` | (Default) Local persistent vector database stored in `./chroma_db`. Perfect for local deployments and testing. |
| **PGVector** | `PGVECTOR` | Postgres integration via `pgvector` and `psycopg2`. Uses OpenAI Embeddings. Requires Postgres DB. |
| **Pinecone** | `PINECONE` | Cloud-native vector search. Uses OpenAI Embeddings and requires `pinecone-client`. |
| **In-Memory** | `IN_MEMORY` | A lightweight Python dictionary mock. Useful for environments where dependencies cannot be installed or for CI/CD pipelines. |

## How to Configure

### 1. Basic (ChromaDB or In-Memory)
1. Open your `.env` file.
2. Set the desired provider:
```env
VECTOR_DB_PROVIDER=CHROMADB
```

### 2. Postgres (PGVector)
If you want to use PostgreSQL for enterprise data persistence:
1. Spin up the Postgres instance using our provided Docker Compose file:
```bash
docker compose -f docker-compose.postgres.yml up -d
```
2. Update your `.env` file to use `PGVECTOR` and provide the connection string:
```env
VECTOR_DB_PROVIDER=PGVECTOR
POSTGRES_URI=postgresql://sentinel:sentinelpass@localhost:5432/sentinel_db
```
> [!NOTE]
> PGVector mode requires `OPENAI_API_KEY` to be set in your `.env` as it uses OpenAI to generate embeddings.

### 3. Pinecone (Cloud)
If you prefer a fully managed cloud vector database:
1. Create a free index on [Pinecone](https://www.pinecone.io/) (Dimensions: 1536, Metric: Cosine).
2. Update your `.env` file to use `PINECONE` and provide your API keys:
```env
VECTOR_DB_PROVIDER=PINECONE
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX_NAME=sentinel-healing-memory
```
> [!NOTE]
> Pinecone mode also requires `OPENAI_API_KEY` to generate embeddings.

## Adding a Custom Vector Database

You can easily write your own database connector. Just implement the `BaseMemoryStore` interface in `src/core/memory_factory.py`.

```python
from src.core.memory_factory import BaseMemoryStore

class CustomVectorStore(BaseMemoryStore):
    def add_memory(self, doc_id: str, memory_doc: str, metadata: dict) -> None:
        # Implementation
        pass

    def query_memory(self, query_str: str, n_results: int = 1) -> str | None:
        # Implementation
        pass

    def delete_memory(self, doc_id: str) -> None:
        # Implementation
        pass
```
Then, register it in the `MemoryFactory.get_memory_store` routing method!
