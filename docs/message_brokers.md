# SentinelCell: Pluggable Message Broker Architecture

SentinelCell implements a unified asynchronous processing system to validate and self-heal inter-agent payloads. To ensure compatibility with diverse enterprise infrastructures, the messaging pipeline is database-agnostic, supporting **Redis MQ**, **Apache Kafka**, and **RabbitMQ** dynamically.

---

## 📑 Supported Brokers

You can configure the active message broker by setting the `MESSAGE_BROKER` environment variable in your `.env` file.

| Broker Provider | Env Value | Python Driver | Delivery Guarantee | Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **Redis MQ** | `REDIS` | `redis.asyncio` | At-Least-Once (via BRPOPLPUSH) | (Default) Low-latency, fast in-memory queueing. |
| **Apache Kafka** | `KAFKA` | `aiokafka` | At-Least-Once / Exactly-Once | Distributed systems, high-throughput commit logging. |
| **RabbitMQ** | `RABBITMQ` | `aio_pika` | At-Least-Once (via manual ACKs) | Complex routing topologies, serverless event hubs. |

---

## ⚙️ Configuration Guides

### 1. Redis MQ Configuration
Redis MQ is the default broker, using a processing queue pattern to ensure no message is lost if a worker crashes mid-validation.

```env
MESSAGE_BROKER=REDIS
REDIS_URL=redis://localhost:6379/0
```

### 2. Apache Kafka Configuration
The Kafka broker runs on high-throughput distributed commits. It disables `enable_auto_commit` to handle offsets manually, committing them only after successful processing.

1. Ensure the Kafka client driver is installed:
   ```bash
   pip install aiokafka
   ```
2. Configure `.env`:
   ```env
   MESSAGE_BROKER=KAFKA
   KAFKA_BOOTSTRAP_SERVERS=localhost:9092
   ```

### 3. RabbitMQ Configuration
RabbitMQ uses durable queues and persistent delivery modes. Prefetch limits are set to `1` to balance execution load among multiple asynchronous workers.

1. Ensure the RabbitMQ driver is installed:
   ```bash
   pip install aio-pika
   ```
2. Configure `.env`:
   ```env
   MESSAGE_BROKER=RABBITMQ
   RABBITMQ_URL=amqp://guest:guest@localhost/
   ```

---

## 🛠️ Adding a Custom Message Broker

To write a custom connector (e.g. for AWS SQS or GCP Pub/Sub), implement the `MessageBroker` abstract interface in [broker_factory.py](file:///Users/atacan/ata-codes/SentinelCell-MAS-Immune-System/src/core/broker_factory.py):

```python
from src.core.broker_factory import MessageBroker
from typing import Tuple, Any, Optional

class CustomMessageBroker(MessageBroker):
    async def push(self, queue_name: str, payload: str):
        # Push message to custom broker
        pass

    async def pop_atomic(self, source_queue: str, processing_queue: str, timeout: int = 5) -> Tuple[Optional[str], Any]:
        # Atomically pop a message and return (payload, ack_token)
        pass

    async def acknowledge(self, processing_queue: str, ack_token: Any):
        # Confirm successful processing (ack, commit offset, delete from queue)
        pass

    async def consume(self, queue_name: str, timeout: int = 0) -> Optional[str]:
        # Direct non-atomic consume
        pass
```

Once written, register your broker class in `BrokerFactory.get_broker()` inside [broker_factory.py](file:///Users/atacan/ata-codes/SentinelCell-MAS-Immune-System/src/core/broker_factory.py).
