# SentinelCell Technical Documentation Directory

Welcome to the technical documentation library for SentinelCell. This index serves as a roadmap to help you navigate our architecture, deployment, and integration patterns.

---

## 📂 Documentation Sitemap

### 🏛️ Architecture & Core Concepts
- **[Mission-Critical Architecture (V3)](file:///Users/atacan/ata-codes/SentinelCell-MAS-Immune-System/docs/mission_critical_architecture.md)**: Deep dive into the Schema Circuit Breaker, Zero-I/O Outbox Pattern, and the Jaccard Dual-Layer Semantic Drift Guard.
- **[Agnostic Logger & Telemetry](file:///Users/atacan/ata-codes/SentinelCell-MAS-Immune-System/docs/agnostic_logger.md)**: Details on structured logging, Prometheus metric collection, and multi-destination log sinks.

### ⚙️ Integration & Storage
- **[Client Integration Guide](file:///Users/atacan/ata-codes/SentinelCell-MAS-Immune-System/docs/client_integration.md)**: Complete guide on how external multi-agent systems interact with the FastAPI API Gateway.
- **[Database Agnostic Schema Registry](file:///Users/atacan/ata-codes/SentinelCell-MAS-Immune-System/docs/schema_registry.md)**: How to configure different database providers (Redis, Postgres, Supabase, SQLite, Mongo, Firestore) for the central Schema Registry.
- **[Vector Database Setup](file:///Users/atacan/ata-codes/SentinelCell-MAS-Immune-System/docs/vector_databases.md)**: Setup and configurations for adaptive memory backends (ChromaDB, PGVector, Pinecone).

### 🚀 Deployment & Operations
- **[Deployment Strategies](file:///Users/atacan/ata-codes/SentinelCell-MAS-Immune-System/docs/deployment_strategies.md)**: Exploring deployment topologies (Middleware SDK Mode, Standalone API Gateway Mode, Distributed MQ Worker Mode).
- **[Docker Setup & Container Policy](file:///Users/atacan/ata-codes/SentinelCell-MAS-Immune-System/docs/docker_setup.md)**: Container security policies, read-only root filesystems, resource limiting, and network isolation policies.
- **[Local Ollama & Offline Setup](file:///Users/atacan/ata-codes/SentinelCell-MAS-Immune-System/docs/local_ollama.md)**: Running SentinelCell in a 100% offline, zero-trust environment with local LLMs (Llama 3/Ollama).
- **[LangChain Models & Provider Fallbacks](file:///Users/atacan/ata-codes/SentinelCell-MAS-Immune-System/docs/langchain_models.md)**: Model factory initialization, API configurations, and model switching priorities.

### 🧪 Quality Assurance & CI/CD
- **[Testing & Coverage Guide](file:///Users/atacan/ata-codes/SentinelCell-MAS-Immune-System/docs/testing_guide.md)**: Running pytest locally, test philosophy, testcontainers integration, and CI/CD coverage enforcement gates.

---

## 🛠️ Getting Started
If you are new to the codebase:
1. Review the root [README.md](file:///Users/atacan/ata-codes/SentinelCell-MAS-Immune-System/README.md) for a high-level overview and Quick Start.
2. Read the **[Deployment Strategies](file:///Users/atacan/ata-codes/SentinelCell-MAS-Immune-System/docs/deployment_strategies.md)** to pick the integration path for your Multi-Agent System.
3. Read the **[Client Integration Guide](file:///Users/atacan/ata-codes/SentinelCell-MAS-Immune-System/docs/client_integration.md)** to begin writing connector code.
