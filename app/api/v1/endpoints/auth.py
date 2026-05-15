from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import reusable_oauth2
from app.core.database import get_db
from app.schemas.user import (
    StandardActionResponse,
    TokenExchangeResponse,
    UserRegistrationResponse,
)
from app.services.auth_service import AuthService

router = APIRouter()

@router.post("/register", response_model=UserRegistrationResponse)
async def register(
    user_in: UserRegistrationResponse,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Any:
    auth_service = AuthService(db)
    return await auth_service.register_user(user_in)

@router.post("/login", response_model=TokenExchangeResponse)
async def login(
    user_in: UserRegistrationResponse,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Any:
    auth_service = AuthService(db)
    return await auth_service.authenticate(user_in.email, user_in.password)

@router.post("/refresh", response_model=TokenExchangeResponse)
async def refresh_token(
    refresh_token_in: str,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Any:
    auth_service = AuthService(db)
    return await auth_service.refresh_access_token(refresh_token_in)

@router.post("/logout", response_model=StandardActionResponse)
async def logout(
    token: Annotated[str, Depends(reusable_oauth2)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Any:
    auth_service = AuthService(db)
    await auth_service.logout(token)
    return StandardActionResponse(
        status="success",
        message="Session revoked successfully"
    )
