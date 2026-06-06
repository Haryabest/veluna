from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_user_flexible
from app.database.session import get_db
from app.repositories.admin_repository import AdminRepository
from app.repositories.generation_repository import PaymentRepository
from app.schemas import UserFinanceStatsResponse, UserResponse
from app.schemas.admin import AdminUserStatsDetailResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(
    user: UserResponse = Depends(get_current_user_flexible),
    session: AsyncSession = Depends(get_db),
):
    return user


@router.get("/balance")
async def get_balance(
    user: UserResponse = Depends(get_current_user_flexible),
    session: AsyncSession = Depends(get_db),
):
    balance = await PaymentRepository(session).get_balance(user.id)
    return {
        "gems": balance.gems if balance else 0,
        "credits": balance.credits if balance else 0,
    }


@router.get("/transactions")
async def list_user_transactions(
    page: int = Query(1, ge=1),
    history_type: str | None = Query(None, alias="type", pattern="^(expense|deposit)$"),
    user: UserResponse = Depends(get_current_user_flexible),
    session: AsyncSession = Depends(get_db),
):
    from app.schemas import PaginatedResponse, TransactionResponse

    repo = PaymentRepository(session)
    transactions, total = await repo.list_transactions(user.id, page=page, kind=history_type)
    page_size = 20
    items = [TransactionResponse.from_transaction(t) for t in transactions]
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/profile", response_model=UserResponse)
async def get_profile(user: UserResponse = Depends(get_current_user)):
    return user


@router.get("/spending", response_model=UserFinanceStatsResponse)
async def get_spending_summary(
    user: UserResponse = Depends(get_current_user_flexible),
    session: AsyncSession = Depends(get_db),
):
    """Balance, spent/deposited totals and purchase stats."""
    raw = await PaymentRepository(session).get_finance_stats(user.id)
    return UserFinanceStatsResponse(**raw)


@router.get("/finance", response_model=UserFinanceStatsResponse)
async def get_finance_stats(
    user: UserResponse = Depends(get_current_user_flexible),
    session: AsyncSession = Depends(get_db),
):
    """Alias for /spending — full financial statistics."""
    raw = await PaymentRepository(session).get_finance_stats(user.id)
    return UserFinanceStatsResponse(**raw)


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
