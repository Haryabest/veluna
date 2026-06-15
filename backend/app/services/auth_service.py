from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.security import create_token_pair, verify_token
from app.core.telegram import TelegramAuthError, validate_telegram_init_data
from app.models import UserRole
from app.models import User
from app.repositories.generation_repository import PaymentRepository
from app.repositories.user_repository import UserRepository
from app.schemas import TokenResponse, UserResponse
from app.services.platform_settings_service import PlatformSettingsService
from app.services.telegram_profile_service import determine_user_avatar_url
from app.services.user_ban_service import ensure_not_banned, refresh_ban_status
from app.utils.locale import locale_from_telegram, normalize_app_locale


class AuthService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._users = UserRepository(session)
        self._settings = get_settings()

    async def authenticate_telegram(self, init_data: str) -> TokenResponse:
        try:
            parsed = validate_telegram_init_data(
                init_data, max_age_seconds=self._settings.telegram_init_data_max_age_seconds
            )
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
                photo_url=determine_user_avatar_url(user_data.get("photo_url")),
                language_code=locale_from_telegram(user_data.get("language_code")),
                locale_selected=False,
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
        else:
            await self._sync_telegram_profile(user, user_data)

        user = await refresh_ban_status(user, self._users)
        ensure_not_banned(user)

        username = (user_data.get("username") or user.username or "").lower()
        is_admin = telegram_id in self._settings.admin_telegram_ids_list
        is_admin = is_admin or (
            username and username in self._settings.admin_telegram_usernames_list
        )
        if is_admin:
            await self._users.update(user, role=UserRole.ADMIN)

        tokens = create_token_pair(user.id)
        return TokenResponse(**tokens.model_dump())

    async def _sync_telegram_profile(self, user: User, user_data: dict) -> None:
        updates: dict = {}

        for field in ("username", "first_name", "last_name"):
            value = user_data.get(field)
            if value is not None and getattr(user, field) != value:
                updates[field] = value

        if not user.locale_selected:
            tg_lang = user_data.get("language_code")
            if tg_lang:
                hint = locale_from_telegram(tg_lang)
                if user.language_code != hint:
                    updates["language_code"] = hint

        init_photo = user_data.get("photo_url")
        photo_url = determine_user_avatar_url(init_photo, user.photo_url)
        if photo_url and user.photo_url != photo_url:
            updates["photo_url"] = photo_url

        if updates:
            await self._users.update(user, **updates)

    async def authenticate_dev(self) -> TokenResponse:
        """Local browser dev only — issue JWT without Telegram WebApp."""
        if self._settings.app_env != "development" and not self._settings.debug:
            raise ForbiddenError("Dev auth is disabled")

        user = None
        if self._settings.dev_telegram_id:
            user = await self._users.get_by_telegram_id(self._settings.dev_telegram_id)
        if not user:
            user = await self._users.get_first_active()
        if not user:
            raise NotFoundError("User", "create a user via Telegram bot /start first")
        user = await refresh_ban_status(user, self._users)
        ensure_not_banned(user)

        tokens = create_token_pair(user.id)
        return TokenResponse(**tokens.model_dump())

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        payload = verify_token(refresh_token, token_type="refresh")
        if not payload:
            raise ForbiddenError("Invalid refresh token")

        user = await self._users.get_by_id(UUID(payload.sub))
        if not user or not user.is_active:
            raise ForbiddenError("User not found or inactive")

        user = await refresh_ban_status(user, self._users)
        ensure_not_banned(user)

        tokens = create_token_pair(user.id)
        return TokenResponse(**tokens.model_dump())

    async def resolve_user(
        self,
        *,
        access_token: str | None = None,
        init_data: str | None = None,
    ) -> UserResponse:
        """Prefer fresh Telegram initData (Mini App), then JWT."""
        init = (init_data or "").strip()
        if init:
            try:
                tokens = await self.authenticate_telegram(init)
                user_id = self._user_id_from_token(tokens.access_token)
                user = await self._users.get_by_id(user_id)
                if not user or not user.is_active:
                    raise ForbiddenError("User not found or inactive")
                return await self._to_user_response(user)
            except ForbiddenError:
                pass
        if access_token:
            return await self.get_current_user(access_token)
        raise ForbiddenError("Invalid or expired token")

    async def resolve_user_id(
        self,
        *,
        access_token: str | None = None,
        init_data: str | None = None,
    ) -> UUID:
        """Like resolve_user but only returns id (avoids lazy-load on balance)."""
        user = await self.resolve_user(
            access_token=access_token,
            init_data=init_data,
        )
        return user.id

    def _user_id_from_token(self, token: str) -> UUID:
        payload = verify_token(token)
        if not payload:
            raise ForbiddenError("Invalid or expired token")
        return UUID(payload.sub)

    async def get_current_user(self, token: str) -> UserResponse:
        user_id = self._user_id_from_token(token)
        user = await self._users.get_by_id(user_id)
        if not user or not user.is_active:
            raise ForbiddenError("User not found or inactive")
        user = await refresh_ban_status(user, self._users)
        ensure_not_banned(user)
        return await self._to_user_response(user)

    async def _to_user_response(self, user: User) -> UserResponse:
        balance = await PaymentRepository(self._session).get_balance(user.id)
        return UserResponse(
            id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            photo_url=user.photo_url,
            language_code=normalize_app_locale(user.language_code),
            locale_selected=user.locale_selected,
            role=user.role.value,
            is_active=user.is_active,
            gems=balance.gems if balance else 0,
            created_at=user.created_at,
        )
