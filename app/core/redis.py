import redis.asyncio as redis
from app.core.config import settings

class RedisClient:
    def __init__(self):
        self.client: redis.Redis | None = None

    async def connect(self):
        self.client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )

    async def disconnect(self):
        if self.client:
            await self.client.close()

    async def set_with_expiry(self, key: str, value: str, expiry: int):
        if self.client:
            await self.client.setex(key, expiry, value)

    async def get(self, key: str) -> str | None:
        if self.client:
            return await self.client.get(key)
        return None

redis_client = RedisClient()

async def get_redis():
    return redis_client
