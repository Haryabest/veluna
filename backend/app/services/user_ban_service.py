"""User ban checks, messages, and admin ban application."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.exceptions import AccountBannedError
from app.models import User
from app.repositories.user_repository import UserRepository

MOSCOW_TZ = timezone(timedelta(hours=3))


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ban_duration_label(banned_until: datetime | None) -> str:
    if banned_until is None:
        return "навсегда"
    dt = banned_until.astimezone(MOSCOW_TZ) if banned_until.tzinfo else banned_until
    return dt.strftime("%d.%m.%Y %H:%M")


def format_ban_message(reason: str | None, banned_until: datetime | None) -> str:
    lines = ["Ваш профиль заблокирован."]
    if reason and reason.strip():
        lines.append(f"Причина: {reason.strip()}")
    if banned_until is None:
        lines.append("Срок: бессрочно")
    else:
        lines.append(f"Блокировка до: {ban_duration_label(banned_until)} (МСК)")
    lines.append("Если это ошибка — напишите администратору в боте.")
    return "\n".join(lines)


def is_ban_active(user: User) -> bool:
    if not user.is_banned:
        return False
    if user.banned_until is None:
        return True
    until = user.banned_until
    if until.tzinfo is None:
        until = until.replace(tzinfo=timezone.utc)
    return until > utc_now()


async def refresh_ban_status(user: User, users: UserRepository) -> User:
    if not user.is_banned or user.banned_until is None:
        return user
    until = user.banned_until
    if until.tzinfo is None:
        until = until.replace(tzinfo=timezone.utc)
    if until <= utc_now():
        return await users.clear_ban(user)
    return user


def ensure_not_banned(user: User) -> None:
    if is_ban_active(user):
        raise AccountBannedError(user.ban_reason, user.banned_until)


def compute_banned_until(duration_days: int | None) -> datetime | None:
    if duration_days is None:
        return None
    return utc_now() + timedelta(days=duration_days)
