from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.database import engine
from app.core.redis import redis_client
from app.models.user import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to Redis
    await redis_client.connect()
    
    # Auto-create tables
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"⚠️ PostgreSQL Error: {e}. Switching to local SQLite...")
        # Emergency fallback engine if Postgres failed at connection time
        fallback_engine = create_async_engine("sqlite+aiosqlite:///./core_auth.db")
        async with fallback_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        # Update the global engine for the rest of the app
        from app.core import database
        database.engine = fallback_engine
        
    yield
    # Shutdown: Close connections
    await redis_client.disconnect()
    await engine.dispose()
