from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, NotFoundError, VelunaError
from app.database.session import get_db
from app.schemas import BaseSchema, TelegramAuthRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter()


class RefreshTokenRequest(BaseSchema):
    refresh_token: str


@router.post("/telegram", response_model=TokenResponse)
async def auth_telegram(data: TelegramAuthRequest, session: AsyncSession = Depends(get_db)):
    service = AuthService(session)
    return await service.authenticate_telegram(data.init_data)


@router.post("/dev", response_model=TokenResponse)
async def auth_dev(session: AsyncSession = Depends(get_db)):
    """Browser localhost: JWT without Telegram initData (development only)."""
    settings = get_settings()
    if settings.app_env != "development" and not settings.debug:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Dev auth is disabled"},
        )
    service = AuthService(session)
    try:
        return await service.authenticate_dev()
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message},
        ) from e
    except ForbiddenError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": e.code, "message": e.message},
        ) from e
    except VelunaError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        ) from e


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    session: AsyncSession = Depends(get_db),
    refresh_token: str | None = Query(None),
    body: RefreshTokenRequest | None = Body(None),
):
    token = (body.refresh_token if body else None) or refresh_token
    if not token:
        from app.core.exceptions import ValidationError

        raise ValidationError("refresh_token is required")
    service = AuthService(session)
    return await service.refresh_token(token)
