from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_user_flexible, security
from app.core.exceptions import ForbiddenError, NotFoundError
from app.database.session import get_db
from app.repositories.admin_repository import AdminRepository
from app.repositories.generation_repository import PaymentRepository
from app.repositories.user_repository import UserRepository
from app.schemas import UserFinanceStatsResponse, UserLocaleUpdate, UserResponse
from app.schemas.admin import AdminUserStatsDetailResponse
from app.services.auth_service import AuthService
from app.services.telegram_profile_service import fetch_user_avatar_bytes
from app.services.user_locale_service import UserLocaleService

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(
    user: UserResponse = Depends(get_current_user_flexible),
    session: AsyncSession = Depends(get_db),
):
    return user


@router.get("/me/avatar")
async def get_my_avatar(
    access_token: str | None = Query(None),
    session: AsyncSession = Depends(get_db),
    x_telegram_init_data: str | None = Header(None, alias="X-Telegram-Init-Data"),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    """Stream Telegram avatar via same-origin URL (for <img src> in Mini App)."""
    auth_service = AuthService(session)
    token = access_token or (credentials.credentials if credentials else None)
    try:
        user = await auth_service.resolve_user(
            access_token=token,
            init_data=x_telegram_init_data,
        )
    except ForbiddenError as exc:
        raise NotFoundError("Avatar", "auth") from exc

    init_photo = None
    if x_telegram_init_data:
        from app.core.telegram import validate_telegram_init_data
        from app.core.config import get_settings

        try:
            parsed = validate_telegram_init_data(
                x_telegram_init_data,
                max_age_seconds=get_settings().telegram_init_data_max_age_seconds,
            )
            init_photo = (parsed.get("user") or {}).get("photo_url")
        except Exception:
            pass

    db_user = await UserRepository(session).get_by_id(user.id)
    if not db_user:
        raise NotFoundError("User", str(user.id))

    avatar = await fetch_user_avatar_bytes(
        telegram_id=db_user.telegram_id,
        photo_url=db_user.photo_url,
        init_photo_url=init_photo,
    )
    if not avatar:
        raise NotFoundError("Avatar", str(user.id))

    data, content_type = avatar
    return Response(
        content=data,
        media_type=content_type,
        headers={"Cache-Control": "private, max-age=300"},
    )


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


@router.patch("/me/locale", response_model=UserResponse)
async def update_my_locale(
    body: UserLocaleUpdate,
    user: UserResponse = Depends(get_current_user_flexible),
    session: AsyncSession = Depends(get_db),
):
    return await UserLocaleService(session).set_locale(user.id, body.language_code)


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
