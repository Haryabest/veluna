import json
from typing import Any

import redis.asyncio as aioredis

from app.core.config import get_settings

settings = get_settings()

redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
cache_client = aioredis.from_url(
    f"{settings.redis_url.rsplit('/', 1)[0]}/{settings.redis_cache_db}",
    decode_responses=True,
)
session_client = aioredis.from_url(
    f"{settings.redis_url.rsplit('/', 1)[0]}/{settings.redis_session_db}",
    decode_responses=True,
)


class RedisCache:
    def __init__(self, client: aioredis.Redis):
        self._client = client

    async def get(self, key: str) -> Any | None:
        value = await self._client.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        serialized = json.dumps(value) if not isinstance(value, str) else value
        await self._client.setex(key, ttl, serialized)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def exists(self, key: str) -> bool:
        return bool(await self._client.get(key))


cache = RedisCache(cache_client)
