from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError
from app.database.session import get_db
from app.schemas import UserResponse
from app.services.auth_service import AuthService

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_REQUIRED", "message": "Not authenticated"},
        )
    auth_service = AuthService(session)
    try:
        return await auth_service.get_current_user(credentials.credentials)
    except ForbiddenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_EXPIRED", "message": e.message},
        ) from e


async def get_current_user_flexible(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    x_telegram_init_data: str | None = Header(None, alias="X-Telegram-Init-Data"),
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Bearer JWT or Telegram initData header (for Mini App after token expiry)."""
    auth_service = AuthService(session)
    try:
        return await auth_service.resolve_user(
            access_token=credentials.credentials if credentials else None,
            init_data=x_telegram_init_data,
        )
    except ForbiddenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_EXPIRED", "message": e.message},
        ) from e


async def get_admin_user(user: UserResponse = Depends(get_current_user)) -> UserResponse:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
