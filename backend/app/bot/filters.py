from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from app.bot.db import bot_session
from app.core.admin_access import is_config_admin
from app.models import UserRole
from app.repositories.user_repository import UserRepository


def _is_config_telegram_admin(user) -> bool:
    """Admin by ADMIN_TELEGRAM_IDS / ADMIN_TELEGRAM_USERNAMES in .env."""
    if not user:
        return False
    return is_config_admin(telegram_id=user.id, username=user.username)


async def is_bot_admin(user) -> bool:
    """Admin from .env or role=admin in database."""
    if not user:
        return False
    if _is_config_telegram_admin(user):
        return True
    async with bot_session() as session:
        db_user = await UserRepository(session).get_by_telegram_id(user.id)
        return db_user is not None and db_user.role == UserRole.ADMIN


# Backward-compatible alias (config only — prefer is_bot_admin in handlers)
def _is_admin_user(user) -> bool:
    return _is_config_telegram_admin(user)


class AdminFilter(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = event.from_user
        return await is_bot_admin(user)
