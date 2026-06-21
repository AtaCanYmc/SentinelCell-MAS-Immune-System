import os
import json
import redis.asyncio as redis


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
        except Exception:
            # Fail silently to avoid interrupting the main immune system loop
            pass


broadcaster = LogBroadcaster()
