from fastapi import APIRouter, Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import security
from app.core.exceptions import ForbiddenError
from app.services.auth_service import AuthService
from app.database.session import get_db
from app.schemas.catalog import ShopProductResponse
from app.schemas.shop import CheckoutRequest, CheckoutResponse, PromoValidateRequest, PromoValidateResponse
from app.services.catalog_service import CatalogService
from app.services.shop_service import ShopService

router = APIRouter()


@router.get("/products", response_model=list[ShopProductResponse])
async def list_shop_products(session: AsyncSession = Depends(get_db)):
    service = CatalogService(session)
    return await service.list_products_public()


@router.post("/promo/validate", response_model=PromoValidateResponse)
async def validate_promo(
    body: PromoValidateRequest,
    session: AsyncSession = Depends(get_db),
):
    service = ShopService(session)
    return await service.validate_promo(body.code)


@router.post("/checkout", response_model=CheckoutResponse)
async def checkout(
    body: CheckoutRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    x_telegram_init_data: str | None = Header(None, alias="X-Telegram-Init-Data"),
    session: AsyncSession = Depends(get_db),
):
    try:
        user_id = await AuthService(session).resolve_user_id(
            access_token=credentials.credentials if credentials else None,
            init_data=body.init_data or x_telegram_init_data,
        )
    except ForbiddenError as e:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_EXPIRED", "message": e.message},
        ) from e
    service = ShopService(session)
    if body.payment_method != "stars":
        from app.core.exceptions import ValidationError

        raise ValidationError("Поддерживается только оплата Telegram Stars")
    return await service.checkout(user_id, body.product_id, body.promo_code)
