from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.security import create_token_pair, verify_token
from app.core.telegram import TelegramAuthError, validate_telegram_init_data
from app.models import UserRole
from app.repositories.user_repository import UserRepository
from app.schemas import TokenResponse, UserResponse
from app.services.platform_settings_service import PlatformSettingsService


class AuthService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._users = UserRepository(session)
        self._settings = get_settings()

    async def authenticate_telegram(self, init_data: str) -> TokenResponse:
        try:
            parsed = validate_telegram_init_data(init_data)
        except TelegramAuthError as e:
            raise ForbiddenError(str(e)) from e

        user_data = parsed.get("user", {})
        telegram_id = user_data.get("id")
        if not telegram_id:
            raise ForbiddenError("Invalid user data in initData")

        user = await self._users.get_by_telegram_id(telegram_id)
        if not user:
            user = await self._users.create(
                telegram_id=telegram_id,
                username=user_data.get("username"),
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name"),
                photo_url=user_data.get("photo_url"),
                language_code=user_data.get("language_code", "en"),
            )
            from app.models import TransactionType
            from app.repositories.generation_repository import PaymentRepository

            payment_repo = PaymentRepository(self._session)
            pricing = await PlatformSettingsService(self._settings).get_pricing()
            await payment_repo.add_gems(
                user.id,
                pricing.default_user_gems,
                tx_type=TransactionType.BONUS,
                description="Welcome bonus",
            )
        elif user.is_banned:
            raise ForbiddenError("Account is banned")

        username = (user_data.get("username") or user.username or "").lower()
        is_admin = telegram_id in self._settings.admin_telegram_ids_list
        is_admin = is_admin or (
            username and username in self._settings.admin_telegram_usernames_list
        )
        if is_admin:
            await self._users.update(user, role=UserRole.ADMIN)

        tokens = create_token_pair(user.id)
        return TokenResponse(**tokens.model_dump())

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        payload = verify_token(refresh_token, token_type="refresh")
        if not payload:
            raise ForbiddenError("Invalid refresh token")

        user = await self._users.get_by_id(UUID(payload.sub))
        if not user or not user.is_active:
            raise ForbiddenError("User not found or inactive")

        tokens = create_token_pair(user.id)
        return TokenResponse(**tokens.model_dump())

    async def get_current_user(self, token: str) -> UserResponse:
        payload = verify_token(token)
        if not payload:
            raise ForbiddenError("Invalid or expired token")

        user = await self._users.get_by_id(UUID(payload.sub))
        if not user or not user.is_active:
            raise ForbiddenError("User not found or inactive")

        balance = user.balance
        return UserResponse(
            id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            photo_url=user.photo_url,
            language_code=user.language_code,
            role=user.role.value,
            is_active=user.is_active,
            gems=balance.gems if balance else 0,
            created_at=user.created_at,
        )
