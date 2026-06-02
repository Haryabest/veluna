from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database.session import get_db
from app.schemas import UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(
    user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return user


@router.get("/profile", response_model=UserResponse)
async def get_profile(user: UserResponse = Depends(get_current_user)):
    return user
