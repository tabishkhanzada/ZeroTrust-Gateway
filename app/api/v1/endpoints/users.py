from typing import Any
from fastapi import APIRouter, Depends
from app.api.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.user import UserRegistrationResponse

router = APIRouter()

@router.get("/me", response_model=UserRegistrationResponse)
async def read_user_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    return current_user
