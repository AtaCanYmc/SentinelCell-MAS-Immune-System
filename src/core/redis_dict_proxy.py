import os
import logging
import orjson
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisDictProxy:
    """
    Lightweight Redis-backed dict proxy that provides async get/set/exists/items semantics
    used by the orchestrator. Values are stored as JSON strings.
    """

    def __init__(self, namespace: str, redis_url: str | None = None):
        self._ns = namespace
        self._redis_url = redis_url or os.getenv(
            "REDIS_URL", "redis://localhost:6379/0"
        )
        try:
            self._client = redis.from_url(self._redis_url)
        except Exception as e:
            logger.error(
                "Failed to initialize RedisDictProxy client for namespace %s: %s",
                namespace,
                e,
            )
            self._client = None

    def _key(self, k: str) -> str:
        return f"{self._ns}:{k}"

    async def get(self, k: str, default=None):
        try:
            if not self._client:
                return default
            val = await self._client.get(self._key(k))
            if not val:
                return default
            return orjson.loads(val)
        except Exception as e:
            logger.error("RedisDictProxy GET failed for key %s: %s", k, e)
            return default

    async def set(self, k: str, v):
        try:
            if not self._client:
                return
            await self._client.set(self._key(k), orjson.dumps(v).decode("utf-8"))
        except Exception as e:
            logger.error("RedisDictProxy SET failed for key %s: %s", k, e)

    async def exists(self, k: str) -> bool:
        try:
            if not self._client:
                return False
            return await self._client.exists(self._key(k)) == 1
        except Exception as e:
            logger.error("RedisDictProxy EXISTS failed for key %s: %s", k, e)
            return False

    async def items(self):
        try:
            if not self._client:
                return {}.items()
            pattern = f"{self._ns}:*"
            keys = [k.decode("utf-8") for k in await self._client.keys(pattern)]
            result = {}
            for full in keys:
                short = full.split(":", 1)[1]
                result[short] = await self.get(short)
            return result.items()
        except Exception as e:
            logger.error(
                "RedisDictProxy ITEMS failed for namespace %s: %s", self._ns, e
            )
            return {}.items()

    async def close(self):
        if self._client:
            try:
                await self._client.aclose()
            except Exception:
                pass
