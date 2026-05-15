import uuid
from datetime import datetime, timezone
from jose import jwt, JWTError
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.core.redis import RedisClient
from app.exceptions.auth import (
    InvalidCredentialsException,
    TokenExpiredException,
    TokenInvalidException,
    UserAlreadyExistsException,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate

class AuthService:
    def __init__(self, user_repo: UserRepository, redis_client: RedisClient):
        self.user_repo = user_repo
        self.redis_client = redis_client

    async def register_user(self, user_in: UserCreate) -> User:
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise UserAlreadyExistsException()
        
        db_user = User(
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
        )
        return await self.user_repo.create(db_user)

    async def authenticate(self, email: str, password: str) -> dict:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsException()
        
        jti_access = str(uuid.uuid4())
        jti_refresh = str(uuid.uuid4())
        
        return {
            "access_token": create_access_token(user.id, jti_access),
            "refresh_token": create_refresh_token(user.id, jti_refresh),
            "token_type": "bearer",
        }

    async def refresh_tokens(self, refresh_token: str) -> dict:
        try:
            payload = jwt.decode(
                refresh_token, settings.REFRESH_TOKEN_SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            if payload.get("token_type") != "refresh":
                raise TokenInvalidException()
            
            user_id = payload.get("sub")
            if not user_id:
                raise TokenInvalidException()
            
            jti_access = str(uuid.uuid4())
            jti_refresh = str(uuid.uuid4())
            
            return {
                "access_token": create_access_token(user_id, jti_access),
                "refresh_token": create_refresh_token(user_id, jti_refresh),
                "token_type": "bearer",
            }
        except jwt.ExpiredSignatureError:
            raise TokenExpiredException()
        except JWTError:
            raise TokenInvalidException()

    async def logout(self, token: str):
        try:
            payload = jwt.decode(
                token, settings.ACCESS_TOKEN_SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                now_ts = int(datetime.now(timezone.utc).timestamp())
                ttl = exp - now_ts
                if ttl > 0:
                    await self.redis_client.set_with_expiry(f"blacklist:{jti}", "true", ttl)
        except JWTError:
            raise TokenInvalidException()
