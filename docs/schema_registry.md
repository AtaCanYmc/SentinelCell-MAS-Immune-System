<div align="center">
  <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/solid/server.svg" width="100" height="100" alt="Schema Registry" style="border-radius: 50%;">

  # SentinelCell: Database Agnostic Schema Registry
</div>

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)
![JSON](https://img.shields.io/badge/json-5E5C5C?style=for-the-badge&logo=json&logoColor=white)

</div>

SentinelCell uses the **Model Context Protocol (MCP)** to serve as a central `SchemaRegistry`. To ensure high availability, distributed synchronization, and zero "Eventual Consistency" issues, SentinelCell implements a **RegistryFactory**. This allows the central schema store to be entirely agnostic to its underlying database.

## Supported Providers

You can switch the active provider by setting the `SCHEMA_REGISTRY_PROVIDER` environment variable in your `.env` file.

| Provider | Configuration Key | Description |
| :--- | :--- | :--- |
| **Redis** | `REDIS` | (Recommended) Distributed, enterprise-ready store. Guarantees strong consistency across multi-node setups and asynchronous workers. |
| **File** | `FILE` | Persistent local file store. Stores schemas in a single `schemas.json` file. Great for simpler, single-node persistence. |
| **In-Memory** | `IN_MEMORY` | A lightweight Python dictionary mock. Useful for rapid testing, local development, and CI/CD pipelines. |

## How to Configure

### 1. Redis (Enterprise/Distributed)
If you want to run multiple instances of SentinelCell (FastAPI + Redis MQ Workers) and ensure they all instantly share the same agent communication contracts:
1. Ensure your Redis container is running.
2. Open your `.env` file and set the provider:
```env
SCHEMA_REGISTRY_PROVIDER=REDIS
REDIS_URL=redis://localhost:6379
```

### 2. File (Persistent Local)
If you want schemas to persist across reboots but don't want to spin up a Redis instance:
1. Update your `.env` file:
```env
SCHEMA_REGISTRY_PROVIDER=FILE
```
> [!NOTE]
> File mode creates a `schemas.json` file in the root directory.

### 3. In-Memory (Ephemeral)
For lightning-fast unit testing where data persistence isn't required:
```env
SCHEMA_REGISTRY_PROVIDER=IN_MEMORY
```

## Adding a Custom Registry Store

You can write your own Registry connector (e.g., PostgreSQL, etcd, or MongoDB). Just implement the `BaseRegistryStore` interface in `src/core/registry_factory.py`.

```python
from src.core.registry_factory import BaseRegistryStore
from typing import Optional

class CustomRegistryStore(BaseRegistryStore):
    async def get_schema(self, agent_id: str) -> Optional[str]:
        # Implementation to fetch schema
        pass

    async def update_schema(self, agent_id: str, schema_json: str) -> None:
        # Implementation to save schema
        pass
```
Then, register it in the `RegistryFactory.get_registry_store()` routing method!
