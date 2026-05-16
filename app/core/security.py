from datetime import UTC, datetime, timedelta
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(subject: str | Any, jti: str) -> str:
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "exp": int(expire.timestamp()),
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "jti": jti,
        "token_type": "access"
    }
    return jwt.encode(to_encode, settings.ACCESS_TOKEN_SECRET_KEY,
                      algorithm=settings.ALGORITHM)

def create_refresh_token(subject: str | Any, jti: str) -> str:
    now = datetime.now(UTC)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "exp": int(expire.timestamp()),
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "jti": jti,
        "token_type": "refresh"
    }
    return jwt.encode(to_encode, settings.REFRESH_TOKEN_SECRET_KEY,
                      algorithm=settings.ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
