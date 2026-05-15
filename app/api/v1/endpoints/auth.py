from typing import Any
from fastapi import APIRouter, Depends, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.auth import get_current_user
from app.core.database import get_db
from app.core.redis import redis_client
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.schemas.user import (
    UserCreate,
    UserRegistrationResponse,
    TokenExchangeResponse,
    StandardActionResponse,
)

router = APIRouter()

@router.post("/register", response_model=UserRegistrationResponse)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo, redis_client)
    return await auth_service.register_user(user_in)

@router.post("/login", response_model=TokenExchangeResponse)
async def login(
    email: str = Body(...),
    password: str = Body(...),
    db: AsyncSession = Depends(get_db)
) -> Any:
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo, redis_client)
    return await auth_service.authenticate(email, password)

@router.post("/refresh", response_model=TokenExchangeResponse)
async def refresh(
    refresh_token: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db)
) -> Any:
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo, redis_client)
    return await auth_service.refresh_tokens(refresh_token)

@router.post("/logout", response_model=StandardActionResponse)
async def logout(
    request: Request,
    current_user: Any = Depends(get_current_user)
) -> Any:
    auth_header = request.headers.get("Authorization")
    token = auth_header.split(" ")[1]
    auth_service = AuthService(None, redis_client) # Repository not needed for logout blacklist
    await auth_service.logout(token)
    return {"detail": "Revocation complete"}
