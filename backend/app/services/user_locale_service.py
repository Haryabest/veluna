from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from app.schemas import UserResponse
from app.services.auth_service import AuthService
from app.utils.locale import normalize_app_locale


class UserLocaleService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._users = UserRepository(session)
        self._auth = AuthService(session)

    async def set_locale(self, user_id: UUID, language_code: str) -> UserResponse:
        locale = normalize_app_locale(language_code)
        user = await self._users.get_by_id(user_id)
        if not user:
            from app.core.exceptions import NotFoundError

            raise NotFoundError("User", str(user_id))
        await self._users.update(
            user,
            language_code=locale,
            locale_selected=True,
        )
        try:
            from app.services.chat_cache_service import chat_cache

            await chat_cache.invalidate_user_lists(user_id)
        except Exception:
            pass
        return await self._auth._to_user_response(user)
