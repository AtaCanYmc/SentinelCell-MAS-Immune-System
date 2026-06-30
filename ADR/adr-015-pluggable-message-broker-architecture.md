# ADR-015: Pluggable Message Broker Architecture (Redis MQ, Apache Kafka, RabbitMQ)

| Metadata | Details |
| :--- | :--- |
| **Date** | 2026-06-28 |
| **Status** | `Accepted` |
| **Author** | SentinelCell Core Architects |
| **Deciders** | Technical Committee & Architecture Board |
| **Relations** | Amends [ADR-006](adr-006-event-driven-architecture.md) |

## Context

In high-throughput enterprise Multi-Agent Systems (MAS), communication workloads vary significantly:
1. Some environments require lightweight, low-overhead in-memory key-value queues (Redis).
2. Heavy financial or healthcare environments require distributed commit logs with **exactly-once / at-least-once delivery guarantees** (Apache Kafka).
3. Complex routing topology setups require rich AMQP-style exchange routing with explicit manual acknowledgments (RabbitMQ).

While [ADR-006](adr-006-event-driven-architecture.md) established the asynchronous worker pattern using Redis, hardcoding the system to Redis MQ limits deployment flexibility and hinders enterprise adoption where Kafka or RabbitMQ are already mandated infrastructure.

## Decision

We designed and implemented a **Pluggable Message Broker Abstraction Layer** managed by a unified `BrokerFactory` (`src/core/broker_factory.py`).

1. **Unified Interface (`MessageBroker`):**
   - Established a base class with abstract methods: `push()`, `pop_atomic()`, `acknowledge()`, and `consume()`.

2. **Atomic Transfer Semantics (`pop_atomic` / `acknowledge`):**
   - **Redis:** Implements `BRPOPLPUSH` for atomic queue transfers (processing queue pattern) and `LREM` for acknowledgments.
   - **Kafka:** Utilizes consumer groups with `enable_auto_commit=False` via the `aiokafka` client, executing explicit offset commits on `acknowledge()` to guarantee at-least-once delivery.
   - **RabbitMQ:** Configures prefetch limits and durable, persistent messages via `aio_pika`. Messages are manually acknowledged with `.ack()` on success, preventing loss during worker crashes.

3. **Pluggable Routing (`BrokerFactory`):**
   - Integrates broker selection via the `MESSAGE_BROKER` environment variable (`REDIS`, `KAFKA`, `RABBITMQ`), allowing code-free runtime adjustments.

## Consequences

### Positive
- **Enterprise Compatibility:** Seamless deployment in environments utilizing different messaging infrastructure.
- **Reliability Guarantees:** Decoupling processing from ingestion, allowing explicit acknowledgement blocks (Kafka offsets, RabbitMQ acks) which prevent payload loss in the event of worker or database failure.
- **Improved Testing:** Simplifies isolation tests since MQ behavior is standardized behind the interface.

### Negative
- **Dependency Complexity:** The Python environment requires multiple client libraries (`redis`, `aiokafka`, `aio_pika`).
- **Feature Parity Gaps:** Kafka does not natively support an atomic queue-to-queue transfer like Redis `BRPOPLPUSH`, meaning the `processing_queue` parameter is bypassed in Kafka implementations, relying on partition offsets instead.
