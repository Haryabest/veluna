from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

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
