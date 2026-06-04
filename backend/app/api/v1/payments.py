from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_user_flexible
from app.database.session import get_db
from app.repositories.generation_repository import PaymentRepository
from app.schemas import PaginatedResponse, PurchaseCreate, TransactionResponse, UserResponse
from app.schemas.shop import TopUpCheckoutRequest, TopUpQuoteRequest, TopUpQuoteResponse
from app.services.shop_service import ShopService

router = APIRouter()


@router.get("/balance")
async def get_balance(
    user: UserResponse = Depends(get_current_user_flexible),
    session: AsyncSession = Depends(get_db),
):
    repo = PaymentRepository(session)
    balance = await repo.get_balance(user.id)
    return {
        "gems": balance.gems if balance else 0,
        "credits": balance.credits if balance else 0,
        "total_spent": balance.total_spent if balance else 0,
        "total_earned": balance.total_earned if balance else 0,
    }


@router.get("/transactions", response_model=PaginatedResponse)
async def list_transactions(
    page: int = Query(1, ge=1),
    history_type: str | None = Query(None, alias="type", pattern="^(expense|deposit)$"),
    user: UserResponse = Depends(get_current_user_flexible),
    session: AsyncSession = Depends(get_db),
):
    repo = PaymentRepository(session)
    transactions, total = await repo.list_transactions(user.id, page=page, kind=history_type)
    page_size = 20
    return PaginatedResponse(
        items=[TransactionResponse.model_validate(t) for t in transactions],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/topup/quote", response_model=TopUpQuoteResponse)
async def topup_quote(
    data: TopUpQuoteRequest,
    user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await ShopService(session).topup_quote(data)


@router.post("/topup/checkout")
async def topup_checkout(
    data: TopUpCheckoutRequest,
    user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await ShopService(session).topup_checkout(user.id, data)


@router.post("/purchase")
async def create_purchase(
    data: PurchaseCreate,
    user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Deprecated: use POST /shop/checkout with product_id for Telegram Stars."""
    from app.core.exceptions import ValidationError

    raise ValidationError("Используйте POST /api/v1/shop/checkout с product_id и payment_method=stars")
