<div align="center">
  <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/solid/shield-halved.svg" width="100" height="100" alt="Mission Critical" style="border-radius: 50%;">

  # SentinelCell: Mission-Critical Architecture (V3)
</div>

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-000000?style=for-the-badge)

</div>

SentinelCell's V3 architecture introduces enterprise-grade "Mission-Critical" and "Zero Fault Tolerance" features. This document outlines the defensive patterns implemented to ensure system stability during massive high-load, network dropouts, and catastrophic failures.

## 1. Schema Circuit Breaker (Stale Cache Fallback)

In a distributed Multi-Agent System (MAS), the Model Context Protocol (MCP) server acts as the central source of truth for validation schemas. However, if the MCP server goes down, the system faces a dilemma:
- **Fail-Open:** Allow all traffic (High security risk).
- **Fail-Closed:** Block all traffic (High operational risk).

**The Solution:** SentinelCell uses a **Circuit Breaker** pattern with a **Stale Cache Fallback**.
When the MCP Registry fails, the system intercepts the exception and checks its local cache. Even if the cached schema has expired (`TTL exceeded`), the Circuit Breaker engages and uses the *Stale Cache* to validate traffic. This ensures the system remains protected and operational without dropping packets during temporary MCP outages.

## 2. Zero-I/O Outbox Pattern

Logging repaired payloads to a Vector Database (like ChromaDB or PGVector) is heavily I/O bound. Under massive load, synchronous database writes within the orchestrator loop create a severe bottleneck.

**The Solution:** SentinelCell implements the **Outbox Pattern**.
1. The LangGraph Orchestrator completes its validation or repair.
2. Instead of writing to the VectorDB, it executes an ultra-fast `LPUSH` command to a Redis queue (`sentinel.outbox`).
3. The gateway returns the repaired payload to the target agent instantly.
4. A separate, asynchronous microservice (`outbox_worker.py`) constantly reads from the Redis queue and safely batches/writes the logs to the VectorDB in the background.

This guarantees that the main API Gateway and Validator Agent never wait for disk I/O, ensuring sub-millisecond latencies.

## 3. Dual-Layer Semantic Drift Guard

When dealing with malformed JSON payloads, Large Language Models (LLMs) are used to "heal" the data structure. However, LLMs are prone to hallucination. A naive repair might fix the JSON syntax but completely alter the original meaning of the data (e.g., changing a transaction amount from 1500 to 0). This is known as **Semantic Drift**.

**The Solution:** A deterministic Dual-Layer Guard.
After the LangChain LLM returns the "repaired" JSON, SentinelCell mathematically compares the atomic values (strings, numbers, booleans) of the original malformed payload with the new repaired payload using a **Jaccard Similarity** calculation.

If the *Value Retention* drops below the strict threshold (e.g., `< 30%`), it means the LLM hallucinated or deleted critical original data. The Semantic Drift Guard immediately rejects the repair and drops the packet, preventing catastrophic data corruption in downstream systems like Core Banking or IoT Ledgers.

## 4. Distributed Quarantine State

When an agent repeatedly sends toxic or unrepairable data, SentinelCell places that specific route into **Quarantine Mode**.

To prevent "Distributed State Vulnerability" (where one load-balanced worker knows about the quarantine but others do not), the quarantine state, error timestamps, and cooldown periods are tracked globally via **Redis Sorted Sets (`ZADD`, `ZREMRANGEBYSCORE`)**. This ensures all SentinelCell instances across the globe synchronously drop malicious traffic the millisecond a threshold is breached.
