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
    AdminUserStatsDetailResponse,
    AdminUserUpdateRequest,
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
from app.schemas.catalog import (
    BroadcastRequest,
    BroadcastResponse,
    PromoCodeCreate,
    PromoCodeResponse,
    PromoCodeUpdate,
    ShopProductCreate,
    ShopProductResponse,
    ShopProductUpdate,
)
from app.services.admin_service import AdminService
from app.services.broadcast_service import BroadcastService
from app.services.catalog_service import CatalogService
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
    q: str | None = Query(None, min_length=1, max_length=100),
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    return await _service(session).list_users(admin.id, page=page, search=q)


@router.get("/users/{user_id}", response_model=AdminUserDetailResponse)
async def get_user(
    user_id: UUID,
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    return await _service(session).get_user(admin.id, user_id)


@router.get("/users/{user_id}/stats", response_model=AdminUserStatsDetailResponse)
async def get_user_stats(
    user_id: UUID,
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    return await _service(session).get_user_stats(admin.id, user_id)


@router.patch("/users/{user_id}", response_model=AdminUserDetailResponse)
async def update_user(
    user_id: UUID,
    body: AdminUserUpdateRequest,
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    return await _service(session).update_user(admin.id, user_id, body)


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


# --- Catalog admin (promos, products, broadcast) ---


@router.get("/promos", response_model=list[PromoCodeResponse])
async def list_promos(
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    await _service(session).verify_admin(admin.id)
    return await CatalogService(session).list_promos()


@router.post("/promos", response_model=PromoCodeResponse)
async def create_promo(
    body: PromoCodeCreate,
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    svc = _service(session)
    await svc.verify_admin(admin.id)
    try:
        promo = await CatalogService(session).create_promo(
            name=body.name,
            discount_percent=body.discount_percent,
            code=body.code,
            max_uses=body.max_uses,
            is_active=body.is_active,
        )
    except ValueError as exc:
        from app.core.exceptions import ValidationError

        raise ValidationError(str(exc)) from exc
    await svc._log(admin.id, "promo_create", "promo", str(promo.id), {"code": promo.code})
    return promo


@router.patch("/promos/{promo_id}", response_model=PromoCodeResponse)
async def update_promo(
    promo_id: UUID,
    body: PromoCodeUpdate,
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    svc = _service(session)
    await svc.verify_admin(admin.id)
    promo = await CatalogService(session).update_promo(
        promo_id, **body.model_dump(exclude_unset=True)
    )
    await svc._log(admin.id, "promo_update", "promo", str(promo_id), body.model_dump(exclude_unset=True))
    return promo


@router.delete("/promos/{promo_id}")
async def delete_promo(
    promo_id: UUID,
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    svc = _service(session)
    await svc.verify_admin(admin.id)
    await CatalogService(session).delete_promo(promo_id)
    await svc._log(admin.id, "promo_delete", "promo", str(promo_id))
    return {"status": "ok"}


@router.get("/products", response_model=list[ShopProductResponse])
async def list_products(
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    await _service(session).verify_admin(admin.id)
    return await CatalogService(session).list_products()


@router.post("/products", response_model=ShopProductResponse)
async def create_product(
    body: ShopProductCreate,
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    from app.models import ShopProductType

    svc = _service(session)
    await svc.verify_admin(admin.id)
    product = await CatalogService(session).create_product(
        name=body.name,
        product_type=ShopProductType(body.product_type),
        price=body.price,
        sale_price=body.sale_price,
        gems_amount=body.gems_amount,
        credits_amount=body.credits_amount,
        is_active=body.is_active,
        sort_order=body.sort_order,
        image_url=body.image_url,
    )
    await svc._log(admin.id, "product_create", "product", str(product.id), {"name": product.name})
    return product


@router.patch("/products/{product_id}", response_model=ShopProductResponse)
async def update_product(
    product_id: UUID,
    body: ShopProductUpdate,
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    svc = _service(session)
    await svc.verify_admin(admin.id)
    product = await CatalogService(session).update_product(
        product_id, **body.model_dump(exclude_unset=True)
    )
    await svc._log(admin.id, "product_update", "product", str(product_id), body.model_dump(exclude_unset=True))
    return product


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: UUID,
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    svc = _service(session)
    await svc.verify_admin(admin.id)
    await CatalogService(session).delete_product(product_id)
    await svc._log(admin.id, "product_delete", "product", str(product_id))
    return {"status": "ok"}


@router.post("/broadcast", response_model=BroadcastResponse)
async def send_broadcast(
    body: BroadcastRequest,
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    svc = _service(session)
    await svc.verify_admin(admin.id)
    record = await BroadcastService(session).send_broadcast(body.message, admin_id=admin.id)
    await svc._log(
        admin.id,
        "broadcast_send",
        "broadcast",
        str(record.id),
        {"sent": record.sent_count, "failed": record.failed_count},
    )
    return BroadcastResponse(
        id=record.id,
        status=record.status,
        total_recipients=record.total_recipients,
        sent_count=record.sent_count,
        failed_count=record.failed_count,
        message_text=record.message_text,
    )


@router.get("/broadcasts", response_model=list[BroadcastResponse])
async def list_broadcasts(
    admin: UserResponse = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    await _service(session).verify_admin(admin.id)
    records = await BroadcastService(session).list_broadcasts()
    return [
        BroadcastResponse(
            id=r.id,
            status=r.status,
            total_recipients=r.total_recipients,
            sent_count=r.sent_count,
            failed_count=r.failed_count,
            message_text=r.message_text[:200],
        )
        for r in records
    ]
