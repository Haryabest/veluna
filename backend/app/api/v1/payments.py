from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database.session import get_db
from app.repositories.generation_repository import PaymentRepository
from app.schemas import PaginatedResponse, PurchaseCreate, TransactionResponse, UserResponse

router = APIRouter()


@router.get("/balance")
async def get_balance(
    user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    repo = PaymentRepository(session)
    balance = await repo.get_balance(user.id)
    return {
        "gems": balance.gems if balance else 0,
        "total_spent": balance.total_spent if balance else 0,
        "total_earned": balance.total_earned if balance else 0,
    }


@router.get("/transactions", response_model=PaginatedResponse)
async def list_transactions(
    page: int = Query(1, ge=1),
    user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    repo = PaymentRepository(session)
    transactions, total = await repo.list_transactions(user.id, page=page)
    page_size = 20
    return PaginatedResponse(
        items=[TransactionResponse.model_validate(t) for t in transactions],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/purchase")
async def create_purchase(
    data: PurchaseCreate,
    user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Telegram Stars purchase — webhook completes the transaction."""
    from app.models import Purchase, PurchaseStatus
    purchase = Purchase(
        user_id=user.id,
        gems_amount=data.gems_amount,
        stars_amount=data.stars_amount,
        status=PurchaseStatus.PENDING,
    )
    session.add(purchase)
    await session.flush()
    return {"purchase_id": str(purchase.id), "status": "pending"}
