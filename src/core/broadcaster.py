import os
import json
import logging
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class LogBroadcaster:
    """
    Asynchronously broadcasts internal SentinelCell logs to Redis PubSub.
    This allows dashboards to subscribe and show real-time agent activity.
    """

    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        self.client = redis.from_url(redis_url)

    async def broadcast(self, message_type: str, content: str):
        payload = {"type": message_type, "content": content}
        try:
            await self.client.publish("sentinel.logs", json.dumps(payload))
        except Exception as e:
            # Log the error but do not raise it to avoid interrupting the main immune system loop
            logger.error("Failed to broadcast log to Redis: %s", e)


broadcaster = LogBroadcaster()
