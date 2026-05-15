import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

logger = logging.getLogger(__name__)

def get_engine_url():
    return settings.DATABASE_URL

# Primary Async Engine
try:
    engine = create_async_engine(
        get_engine_url(),
        echo=False,
        pool_size=10,
        max_overflow=20,
        future=True
    )
except Exception:
    logger.warning(
        "PostgreSQL connection failed. Falling back to local SQLite."
    )
    engine = create_async_engine("sqlite+aiosqlite:///./core_auth.db")

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
