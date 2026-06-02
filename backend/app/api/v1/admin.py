from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_admin_user
from app.database.session import get_db
from app.schemas import (
    CharacterCreate,
    CharacterDetailResponse,
    CharacterUpdate,
    PaginatedResponse,
    UserResponse,
)
from app.schemas.admin import (
    AdminStatsResponse,
    AdminUserDetailResponse,
    AnalyticsSummaryResponse,
    ApiUsageResponse,
    CharacterMediaConfirmRequest,
    CharacterMediaUploadRequest,
    CharacterMediaUploadResponse,
    GemAdjustRequest,
    PricingConfigResponse,
    PricingConfigUpdate,
    UserBanRequest,
)
from app.services.admin_service import AdminService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def _service(session: AsyncSession) -> AdminService:
    return AdminService(session)


@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats(
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    return await _service(session).get_stats(admin.id)


@router.get("/users", response_model=PaginatedResponse)
async def list_users(
    page: int = Query(1, ge=1),
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    return await _service(session).list_users(admin.id, page=page)


@router.get("/users/{user_id}", response_model=AdminUserDetailResponse)
async def get_user(
    user_id: UUID,
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    return await _service(session).get_user(admin.id, user_id)


@router.patch("/users/{user_id}/ban", response_model=AdminUserDetailResponse)
async def ban_user(
    user_id: UUID,
    body: UserBanRequest,
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    return await _service(session).set_user_ban(admin.id, user_id, body.is_banned)


@router.post("/users/{user_id}/gems")
async def adjust_user_gems(
    user_id: UUID,
    body: GemAdjustRequest,
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    await _service(session).adjust_gems(admin.id, user_id, body.amount, body.description)
    return {"status": "ok"}


@router.get("/characters", response_model=PaginatedResponse)
async def list_characters(
    page: int = Query(1, ge=1),
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    return await _service(session).list_characters(admin.id, page=page)


@router.get("/characters/{character_id}", response_model=CharacterDetailResponse)
async def get_character(
    character_id: UUID,
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    return await _service(session).get_character(admin.id, character_id)


@router.post("/characters", response_model=CharacterDetailResponse)
async def create_character(
    data: CharacterCreate,
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    return await _service(session).create_character(admin.id, data)


@router.patch("/characters/{character_id}", response_model=CharacterDetailResponse)
async def update_character(
    character_id: UUID,
    data: CharacterUpdate,
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    return await _service(session).update_character(admin.id, character_id, data)


@router.delete("/characters/{character_id}")
async def delete_character(
    character_id: UUID,
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    await _service(session).delete_character(admin.id, character_id)
    return {"status": "ok"}


@router.post(
    "/characters/{character_id}/media/upload-url",
    response_model=CharacterMediaUploadResponse,
)
async def character_media_upload_url(
    character_id: UUID,
    body: CharacterMediaUploadRequest,
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    return await _service(session).request_media_upload(admin.id, character_id, body)


@router.post("/characters/{character_id}/media/confirm", response_model=CharacterDetailResponse)
async def character_media_confirm(
    character_id: UUID,
    body: CharacterMediaConfirmRequest,
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    return await _service(session).confirm_media(admin.id, character_id, body)


@router.get("/transactions", response_model=PaginatedResponse)
async def list_transactions(
    page: int = Query(1, ge=1),
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    return await _service(session).list_transactions(admin.id, page=page)


@router.get("/analytics", response_model=list[AnalyticsSummaryResponse])
async def analytics_summary(
    days: int = Query(7, ge=1, le=90),
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    return await _service(session).analytics_summary(admin.id, days=days)


@router.get("/api-usage", response_model=ApiUsageResponse)
async def api_usage(
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    return await _service(session).api_usage(admin.id)


@router.get("/pricing", response_model=PricingConfigResponse)
async def get_pricing(
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    return await _service(session).get_pricing(admin.id)


@router.patch("/pricing", response_model=PricingConfigResponse)
async def update_pricing(
    body: PricingConfigUpdate,
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    return await _service(session).update_pricing(admin.id, body)


@router.get("/logs", response_model=PaginatedResponse)
async def list_admin_logs(
    page: int = Query(1, ge=1),
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    return await _service(session).list_logs(admin.id, page=page)
