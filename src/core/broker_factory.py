import os
from abc import ABC, abstractmethod


from typing import Any, Tuple, Optional


class MessageBroker(ABC):
    @abstractmethod
    async def push(self, queue_name: str, payload: str):
        """Pushes a message to the specified queue."""
        pass

    @abstractmethod
    async def pop_atomic(
        self, source_queue: str, processing_queue: str, timeout: int = 5
    ) -> Tuple[Optional[str], Any]:
        """
        Atomically pops from source and pushes to processing queue.
        Returns a tuple of (payload, ack_token) or (None, None) if timeout.
        """
        pass

    @abstractmethod
    async def acknowledge(self, processing_queue: str, ack_token: Any):
        """
        Acknowledges a message (e.g. removes it from processing queue or commits offset).
        The ack_token is the opaque token returned by pop_atomic.
        """
        pass

    @abstractmethod
    async def consume(self, queue_name: str, timeout: int = 0) -> str | None:
        """
        Consumes a message from the queue directly (used for Ingress).
        """
        pass


class RedisBroker(MessageBroker):
    def __init__(self):
        import redis.asyncio as redis

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.r = redis.from_url(redis_url)

    async def push(self, queue_name: str, payload: str):
        await self.r.lpush(queue_name, payload)

    async def pop_atomic(
        self, source_queue: str, processing_queue: str, timeout: int = 5
    ) -> Tuple[Optional[str], Any]:
        payload = await self.r.brpoplpush(
            source_queue, processing_queue, timeout=timeout
        )
        # For Redis, the payload itself acts as the ack_token for LREM
        return payload, payload

    async def acknowledge(self, processing_queue: str, ack_token: Any):
        if ack_token:
            await self.r.lrem(processing_queue, 1, ack_token)

    async def consume(self, queue_name: str, timeout: int = 0) -> str | None:
        res = await self.r.blpop(queue_name, timeout=timeout)
        if res:
            return res[1].decode("utf-8")
        return None


class KafkaBroker(MessageBroker):
    def __init__(self):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.producer = None
        self.consumers = {}

    async def _get_producer(self):
        from aiokafka import AIOKafkaProducer

        if not self.producer:
            self.producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers)
            await self.producer.start()
        return self.producer

    async def _get_consumer(self, topic: str, group_id: str):
        from aiokafka import AIOKafkaConsumer

        key = f"{topic}_{group_id}"
        if key not in self.consumers:
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=group_id,
                enable_auto_commit=False,  # We handle commits explicitly for exactly-once guarantees
                auto_offset_reset="earliest",
            )
            await consumer.start()
            self.consumers[key] = consumer
        return self.consumers[key]

    async def push(self, queue_name: str, payload: str):
        producer = await self._get_producer()
        await producer.send_and_wait(queue_name, payload.encode("utf-8"))

    async def pop_atomic(
        self, source_queue: str, processing_queue: str, timeout: int = 5
    ) -> Tuple[Optional[str], Any]:
        # Kafka's atomic transfer is handled via Consumer Groups and explicit commits.
        # The processing_queue parameter is ignored in Kafka context.
        consumer = await self._get_consumer(
            source_queue, group_id=f"{source_queue}_workers"
        )
        try:
            from aiokafka import OffsetAndMetadata

            msg_dict = await consumer.getmany(timeout_ms=timeout * 1000, max_records=1)
            for tp, msgs in msg_dict.items():
                if msgs:
                    msg = msgs[0]
                    # The ack_token is a dict containing consumer reference and offset info
                    ack_token = {
                        "consumer": consumer,
                        "offsets": {tp: OffsetAndMetadata(msg.offset + 1, "")},
                    }
                    return msg.value.decode("utf-8"), ack_token
            return None, None
        except Exception:
            return None, None

    async def acknowledge(self, processing_queue: str, ack_token: Any):
        if ack_token and isinstance(ack_token, dict) and "consumer" in ack_token:
            consumer = ack_token["consumer"]
            offsets = ack_token["offsets"]
            await consumer.commit(offsets)

    async def consume(self, queue_name: str, timeout: int = 0) -> str | None:
        # Same logic as pop_atomic but maybe different group
        payload, _ = await self.pop_atomic(
            queue_name, processing_queue="", timeout=timeout if timeout > 0 else 1
        )
        return payload


class RabbitMQBroker(MessageBroker):
    def __init__(self):
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
        self.connection = None
        self.channel = None
        self._unacked_messages = {}

    async def _get_channel(self):
        import aio_pika

        if not self.connection:
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
        if not self.channel:
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=1)
        return self.channel

    async def push(self, queue_name: str, payload: str):
        import aio_pika

        channel = await self._get_channel()
        await channel.declare_queue(queue_name, durable=True)
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=payload.encode("utf-8"),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=queue_name,
        )

    async def pop_atomic(
        self, source_queue: str, processing_queue: str, timeout: int = 5
    ) -> Tuple[Optional[str], Any]:
        import asyncio
        import aio_pika

        channel = await self._get_channel()
        queue = await channel.declare_queue(source_queue, durable=True)

        end_time = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < end_time:
            try:
                message = await queue.get(no_ack=False, timeout=1)
                payload = message.body.decode("utf-8")
                # Return the actual message object as the ack_token
                return payload, message
            except aio_pika.exceptions.QueueEmpty:
                await asyncio.sleep(0.5)
        return None, None

    async def acknowledge(self, processing_queue: str, ack_token: Any):
        if ack_token:
            await ack_token.ack()

    async def consume(self, queue_name: str, timeout: int = 0) -> str | None:
        import aio_pika

        channel = await self._get_channel()
        queue = await channel.declare_queue(queue_name, durable=True)

        try:
            message = await queue.get(
                no_ack=True, timeout=timeout if timeout > 0 else 1
            )
            return message.body.decode("utf-8")
        except aio_pika.exceptions.QueueEmpty:
            return None


class BrokerFactory:
    _instance = None

    @classmethod
    def get_broker(cls) -> MessageBroker:
        if cls._instance is None:
            provider = os.getenv("MESSAGE_BROKER", "REDIS").upper()
            if provider == "KAFKA":
                cls._instance = KafkaBroker()
            elif provider == "RABBITMQ":
                cls._instance = RabbitMQBroker()
            else:
                cls._instance = RedisBroker()
        return cls._instance
