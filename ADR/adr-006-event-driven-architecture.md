# ADR-006: Event-Driven Architecture with Redis MQ & FastAPI

## Status
**Accepted**

## Context
SentinelCell acts as an Immune System, intercepting vast amounts of communication packets between agents in a Multi-Agent System (MAS). Validating each packet using an LLM synchronously would block the main gateway, causing catastrophic bottlenecks and timeouts in the overall system.

## Decision
We adopted an **Event-Driven Asynchronous Architecture**:
1. A **FastAPI Gateway** (`src/gateways/fastapi_gateway.py`) intercepts the traffic and immediately returns a `202 Accepted` or forwards it, offloading the heavy validation work.
2. The packet is pushed to a **Redis Message Queue** (Redis MQ).
3. Background workers (`src/gateways/redis_mq.py`) consume the queue asynchronously, executing the LangGraph `Validator Agent`.

## Rationale
1. **High Throughput**: The gateway remains lightning-fast, capable of absorbing massive traffic spikes without blocking.
2. **Scalability**: We can spin up multiple independent Redis MQ worker containers to parallelize the LLM validation load across distributed nodes.
3. **Fault Tolerance**: If an LLM request times out or a worker crashes, the packet remains in the queue (or dead-letter queue) and can be retried without losing the intercepted data.

## Consequences
- **Positive**: Horizontally scalable, highly performant, non-blocking ingestion.
- **Negative**: Adds architectural complexity. Requires a running Redis instance to manage the queues. "Eventual consistency" means malicious packets might reach the destination milliseconds before the Immune System can flag and quarantine the sender.
