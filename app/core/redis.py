import redis.asyncio as redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self.client: redis.Redis | None = None

    async def connect(self):
        try:
            self.client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2  # Short timeout to avoid hanging
            )
            # Test connection immediately
            await self.client.ping()
            logger.info("✅ Redis connected successfully.")
        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable at startup: {e}. Falling back to non-blocking mode.")
            self.client = None

    async def disconnect(self):
        if self.client:
            try:
                await self.client.close()
            except:
                pass

    async def set_with_expiry(self, key: str, value: str, expiry: int):
        if self.client:
            try:
                await self.client.setex(key, expiry, value)
            except Exception as e:
                logger.error(f"❌ Failed to set Redis key {key}: {e}")

    async def get(self, key: str) -> str | None:
        if self.client:
            try:
                return await self.client.get(key)
            except Exception as e:
                logger.error(f"❌ Failed to get Redis key {key}: {e}")
                return None
        return None

redis_client = RedisClient()

async def get_redis():
    return redis_client
