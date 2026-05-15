from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import engine
from app.core.redis import redis_client
from app.models.user import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to Redis and Initialize DB
    await redis_client.connect()
    
    # Auto-create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield
    # Shutdown: Close connections
    await redis_client.disconnect()
    await engine.dispose()
