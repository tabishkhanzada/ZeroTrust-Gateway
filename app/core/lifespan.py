from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import engine
from app.core.redis import redis_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to Redis
    await redis_client.connect()
    yield
    # Shutdown: Close connections
    await redis_client.disconnect()
    await engine.dispose()
