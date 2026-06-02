from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user
from app.database.session import get_db
from app.models import AnalyticsEvent, Generation, Message, User
from app.schemas import (
    AdminStatsResponse,
    CharacterCreate,
    CharacterDetailResponse,
    CharacterUpdate,
    PaginatedResponse,
    UserResponse,
)
from app.services.character_service import AdminService

router = APIRouter()


@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats(
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    total_users = (await session.execute(select(func.count(User.id)))).scalar_one()
    total_messages = (await session.execute(select(func.count(Message.id)))).scalar_one()
    total_generations = (await session.execute(select(func.count(Generation.id)))).scalar_one()
    return AdminStatsResponse(
        total_users=total_users,
        active_users_24h=0,
        total_messages=total_messages,
        total_generations=total_generations,
        total_revenue_gems=0,
    )


@router.get("/users", response_model=PaginatedResponse)
async def list_users(
    page: int = Query(1, ge=1),
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    service = AdminService(session)
    return await service.list_users(admin.id, page=page)


@router.post("/characters", response_model=CharacterDetailResponse)
async def create_character(
    data: CharacterCreate,
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    service = AdminService(session)
    return await service.create_character(admin.id, data)


@router.patch("/characters/{character_id}", response_model=CharacterDetailResponse)
async def update_character(
    character_id: UUID,
    data: CharacterUpdate,
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    service = AdminService(session)
    return await service.update_character(admin.id, character_id, data)


@router.post("/users/{user_id}/gems")
async def adjust_user_gems(
    user_id: UUID,
    amount: int,
    description: str = "Admin adjustment",
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    service = AdminService(session)
    await service.adjust_gems(admin.id, user_id, amount, description)
    return {"status": "ok"}
