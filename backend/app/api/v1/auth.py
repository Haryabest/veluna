from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas import TelegramAuthRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/telegram", response_model=TokenResponse)
async def auth_telegram(data: TelegramAuthRequest, session: AsyncSession = Depends(get_db)):
    service = AuthService(session)
    return await service.authenticate_telegram(data.init_data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, session: AsyncSession = Depends(get_db)):
    service = AuthService(session)
    return await service.refresh_token(refresh_token)
