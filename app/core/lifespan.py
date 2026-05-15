from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.database import engine
from app.core.redis import redis_client
from app.models.user import Base
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
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
        logger.warning(f"⚠️ PostgreSQL Error: {e}. Switching to local SQLite for 'Perfect' demo.")
        # Emergency fallback engine
        fallback_engine = create_async_engine("sqlite+aiosqlite:///./core_auth.db")
        async with fallback_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Inject fallback engine into the global state
        from app.core import database
        database.engine = fallback_engine
        current_engine = fallback_engine

    yield

    # --- Shutdown ---
    try:
        await redis_client.disconnect()
    except:
        pass
        
    try:
        await current_engine.dispose()
    except:
        pass
