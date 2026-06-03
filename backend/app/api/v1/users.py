from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_user_flexible
from app.database.session import get_db
from app.repositories.admin_repository import AdminRepository
from app.schemas import UserResponse
from app.schemas.admin import AdminUserStatsDetailResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(
    user: UserResponse = Depends(get_current_user_flexible),
    session: AsyncSession = Depends(get_db),
):
    return user


@router.get("/profile", response_model=UserResponse)
async def get_profile(user: UserResponse = Depends(get_current_user)):
    return user


@router.get("/me/stats", response_model=AdminUserStatsDetailResponse)
async def get_my_stats(
    user: UserResponse = Depends(get_current_user_flexible),
    session: AsyncSession = Depends(get_db),
):
    raw = await AdminRepository(session).get_user_stats(user.id)
    if not raw:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("User", str(user.id))
    return AdminUserStatsDetailResponse(**raw)
