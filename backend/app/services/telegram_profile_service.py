"""Telegram user avatar — determine source URL and stream via API proxy (no MinIO)."""

from __future__ import annotations

import httpx
from aiogram import Bot

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_LEGACY_MIRROR_MARKERS = ("/media/users/", "/media/previews/avatars/")

_TELEGRAM_AVATAR_MARKERS = (
    "t.me/i/userpic",
    "telegram.org",
    "telegram.me",
    "api.telegram.org/file/",
)

_CONTENT_TYPE_BY_EXT = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}


def normalize_avatar_url(url: str | None) -> str | None:
    if not url:
        return None
    trimmed = str(url).strip()
    return trimmed or None


def is_legacy_mirror_url(url: str | None) -> bool:
    """Old MinIO mirror paths that 403 in Telegram WebView."""
    if not url:
        return False
    lower = url.lower()
    return any(marker in lower for marker in _LEGACY_MIRROR_MARKERS)


def is_telegram_avatar_url(url: str | None) -> bool:
    if not url:
        return False
    lower = url.lower()
    return any(marker in lower for marker in _TELEGRAM_AVATAR_MARKERS)


def determine_user_avatar_url(
    init_photo_url: str | None,
    stored_photo_url: str | None = None,
) -> str | None:
    """Pick the best avatar URL for a user (initData first, then DB).

    Skips legacy MinIO mirror paths. Returns None when only broken URLs exist.
    """
    for candidate in (init_photo_url, stored_photo_url):
        url = normalize_avatar_url(candidate)
        if url and not is_legacy_mirror_url(url):
            return url
    return None


def pick_telegram_photo_url(
    init_photo_url: str | None,
    existing_photo_url: str | None = None,
) -> str | None:
    """Backward-compatible alias for :func:`determine_user_avatar_url`."""
    return determine_user_avatar_url(init_photo_url, existing_photo_url)


def _content_type_for_path(file_path: str) -> str:
    ext = file_path.rsplit(".", 1)[-1].lower()
    return _CONTENT_TYPE_BY_EXT.get(ext, "image/jpeg")


async def _fetch_avatar_bytes_via_bot(telegram_id: int) -> tuple[bytes, str] | None:
    """Download profile photo via aiogram Bot API (same as bot.get_user_profile_photos)."""
    settings = get_settings()
    token = settings.telegram_bot_token.strip()
    if not token:
        return None

    bot = Bot(token=token)
    try:
        user_photos = await bot.get_user_profile_photos(user_id=telegram_id, limit=1)
        if user_photos.total_count <= 0 or not user_photos.photos:
            return None

        photo_file_id = user_photos.photos[0][-1].file_id
        tg_file = await bot.get_file(photo_file_id)
        if not tg_file.file_path:
            return None

        buffer = await bot.download_file(tg_file.file_path)
        if buffer is None:
            return None

        data = buffer.getvalue()
        return data, _content_type_for_path(tg_file.file_path)
    except Exception:
        logger.warning("Failed to fetch Telegram avatar via bot for %s", telegram_id, exc_info=True)
        return None
    finally:
        await bot.session.close()


async def _bot_api_avatar_url(telegram_id: int) -> str | None:
    settings = get_settings()
    token = settings.telegram_bot_token.strip()
    if not token:
        return None

    bot = Bot(token=token)
    try:
        user_photos = await bot.get_user_profile_photos(user_id=telegram_id, limit=1)
        if user_photos.total_count <= 0 or not user_photos.photos:
            return None

        photo_file_id = user_photos.photos[0][-1].file_id
        tg_file = await bot.get_file(photo_file_id)
        if not tg_file.file_path:
            return None
        return f"https://api.telegram.org/file/bot{token}/{tg_file.file_path}"
    except Exception:
        logger.warning("Failed to resolve Telegram avatar URL for %s", telegram_id, exc_info=True)
        return None
    finally:
        await bot.session.close()


async def fetch_user_avatar_bytes(
    *,
    telegram_id: int,
    photo_url: str | None = None,
    init_photo_url: str | None = None,
) -> tuple[bytes, str] | None:
    """Fetch avatar bytes: Bot API first (reliable), then initData/DB URL fallback."""
    bot_avatar = await _fetch_avatar_bytes_via_bot(telegram_id)
    if bot_avatar:
        return bot_avatar

    source_url = determine_user_avatar_url(init_photo_url, photo_url)
    if not source_url:
        return None

    try:
        return await fetch_avatar_bytes(source_url)
    except Exception:
        logger.warning(
            "Failed to fetch Telegram avatar from URL for %s",
            telegram_id,
            exc_info=True,
        )
        return None


async def resolve_user_avatar_fetch_url(
    *,
    telegram_id: int,
    photo_url: str | None = None,
    init_photo_url: str | None = None,
) -> str | None:
    """Resolve URL to download avatar bytes from (Bot API, Telegram CDN, or external)."""
    bot_url = await _bot_api_avatar_url(telegram_id)
    if bot_url:
        return bot_url

    picked = determine_user_avatar_url(init_photo_url, photo_url)
    if picked:
        return picked
    return None


async def resolve_avatar_source_url(
    *,
    telegram_id: int,
    photo_url: str | None,
    init_photo_url: str | None = None,
) -> str | None:
    """Backward-compatible alias for :func:`resolve_user_avatar_fetch_url`."""
    return await resolve_user_avatar_fetch_url(
        telegram_id=telegram_id,
        photo_url=photo_url,
        init_photo_url=init_photo_url,
    )


async def fetch_avatar_bytes(source_url: str) -> tuple[bytes, str]:
    async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
        resp = await client.get(source_url)
        resp.raise_for_status()
        content_type = (resp.headers.get("content-type") or "image/jpeg").split(";", 1)[0].lower()
        if "svg" in content_type or source_url.lower().endswith(".svg"):
            content_type = "image/svg+xml"
        return resp.content, content_type
