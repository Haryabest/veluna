"""Shared admin checks: DB role or TELEGRAM_WEBAPP admin list from settings."""

from app.core.config import Settings, get_settings
from app.models import User, UserRole
from app.repositories.user_repository import UserRepository


def is_config_admin(
    *,
    telegram_id: int,
    username: str | None,
    settings: Settings | None = None,
) -> bool:
    cfg = settings or get_settings()
    if telegram_id in cfg.admin_telegram_ids_list:
        return True
    uname = (username or "").lower()
    return bool(uname and uname in cfg.admin_telegram_usernames_list)


async def ensure_db_admin(user: User, users: UserRepository) -> bool:
    """Promote config-listed admins in DB; return True if user may run admin actions."""
    if user.role == UserRole.ADMIN:
        return True
    if is_config_admin(telegram_id=user.telegram_id, username=user.username):
        await users.update(user, role=UserRole.ADMIN)
        return True
    return False
