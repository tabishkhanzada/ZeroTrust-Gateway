from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import redis_client

router = APIRouter()

@router.get("/status")
async def get_system_status(db: AsyncSession = Depends(get_db)) -> Any:
    # Check Database
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    # Check Redis
    redis_ok = False
    if redis_client.client:
        try:
            await redis_client.client.ping()
            redis_ok = True
        except Exception:
            redis_ok = False

    return {
        "status": "operational" if db_ok else "degraded",
        "database": "connected" if db_ok else "fallback_mode",
        "redis": "connected" if redis_ok else "unavailable",
        "version": "1.4.2-Enterprise"
    }
