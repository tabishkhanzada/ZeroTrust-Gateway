
import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models.user import Base

# Test Database: use the CI-provisioned DB on GitHub, SQLite locally
if os.getenv("GITHUB_ACTIONS"):
    TEST_DATABASE_URL = settings.DATABASE_URL
else:
    TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"



from unittest.mock import AsyncMock, MagicMock
from app.core.redis import RedisClient

class MockRedis:
    def __init__(self):
        self.data = {}
    async def setex(self, key, expiry, value):
        self.data[key] = value
    async def get(self, key):
        return self.data.get(key)
    async def close(self):
        pass
    async def ping(self):
        return True
    async def flushdb(self):
        self.data.clear()

class MockRedisClient:
    def __init__(self):
        self.client = MockRedis()
    async def connect(self):
        pass
    async def disconnect(self):
        pass
    async def set_with_expiry(self, key, value, expiry):
        await self.client.setex(key, expiry, value)
    async def get(self, key):
        return await self.client.get(key)
    async def flush(self):
        await self.client.flushdb()

@pytest.fixture(scope="session")
def mock_redis():
    return MockRedisClient()

@pytest.fixture(scope="function")
async def db_engine():
    """Create a fresh engine per test function to avoid cross-loop issues."""
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine):
    session_factory = async_sessionmaker(
        bind=db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def client(db_session, mock_redis):
    async def override_get_db():
        yield db_session
    
    # Reset mock redis for each test
    await mock_redis.flush()

    from app.core.database import get_db
    from app.core.redis import get_redis, redis_client
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = lambda: mock_redis
    
    # Patch the existing singleton's methods so all modules see the mock
    old_get = redis_client.get
    old_set = redis_client.set_with_expiry
    
    redis_client.get = mock_redis.get
    redis_client.set_with_expiry = mock_redis.set_with_expiry

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    
    redis_client.get = old_get
    redis_client.set_with_expiry = old_set
    app.dependency_overrides.clear()
