from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import RedisClient, redis_client
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
    token: Annotated[str, Depends(reusable_oauth2)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[RedisClient, Depends(lambda: redis_client)]
) -> User:
    try:
        payload = jwt.decode(
            token,
            settings.ACCESS_TOKEN_SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"leeway": 30}
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
        raise TokenExpiredException() from None
    except JWTError:
        raise TokenInvalidException() from None

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(int(user_id))
    if not user:
        raise TokenInvalidException()
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise TokenInvalidException()
    return current_user
