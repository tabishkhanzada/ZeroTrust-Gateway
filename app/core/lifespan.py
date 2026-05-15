import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.database import engine
from app.core.redis import redis_client
from app.models.user import Base

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # --- Redis Startup ---
    try:
        await redis_client.connect()
        logger.info("✅ Redis connected successfully.")
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {e}. Token blacklisting will be unavailable.")

    # --- Database Startup ---
    current_engine = engine
    try:
        # Test connection and create tables
        async with current_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ PostgreSQL tables initialized.")
    except Exception as e:
        logger.warning(
            f"⚠️ PostgreSQL Error: {e}. Switching to local SQLite..."
        )
        # Emergency fallback engine if Postgres failed at connection time
        fallback_engine = create_async_engine(
            "sqlite+aiosqlite:///./core_auth.db"
        )
        async with fallback_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        # Update the global engine for the rest of the app
        from app.core import database
        database.engine = fallback_engine
        current_engine = fallback_engine

    yield

    # Shutdown: Close connections
    try:
        await redis_client.disconnect()
    except Exception:
        pass

    try:
        await current_engine.dispose()
    except Exception:
        pass
