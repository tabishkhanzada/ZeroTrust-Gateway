from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.redis import redis_client, RedisClient
from app.exceptions.auth import (
    TokenBlacklistedException,
    TokenExpiredException,
    TokenInvalidException,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_current_user(
    token: str = Depends(reusable_oauth2),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(lambda: redis_client)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.ACCESS_TOKEN_SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        jti = payload.get("jti")
        if not jti:
            raise TokenInvalidException()
        
        # Check blacklist
        is_blacklisted = await redis.get(f"blacklist:{jti}")
        if is_blacklisted:
            raise TokenBlacklistedException()

        user_id: str = payload.get("sub")
        if user_id is None:
            raise TokenInvalidException()
    except jwt.ExpiredSignatureError:
        raise TokenExpiredException()
    except JWTError:
        raise TokenInvalidException()

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(int(user_id))
    if not user:
        raise TokenInvalidException()
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise TokenInvalidException()
    return current_user
