from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from app.core.config import get_settings


def _is_admin_user(user) -> bool:
    if not user:
        return False
    settings = get_settings()
    if user.id in settings.admin_telegram_ids_list:
        return True
    username = (user.username or "").lower()
    return bool(username and username in settings.admin_telegram_usernames_list)


class AdminFilter(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = event.from_user
        return _is_admin_user(user)
