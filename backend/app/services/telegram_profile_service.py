"""Telegram profile photo — stream via API proxy (no MinIO storage)."""

from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def pick_telegram_photo_url(
    init_photo_url: str | None,
    existing_photo_url: str | None = None,
) -> str | None:
    if init_photo_url and str(init_photo_url).strip():
        return str(init_photo_url).strip()
    if existing_photo_url and str(existing_photo_url).strip():
        return str(existing_photo_url).strip()
    return None


def is_telegram_cdn_url(url: str | None) -> bool:
    if not url:
        return False
    lower = url.lower()
    return (
        "t.me/i/userpic" in lower
        or "telegram.org" in lower
        or "telegram.me" in lower
        or "api.telegram.org/file/" in lower
    )


async def _bot_profile_photo_url(telegram_id: int) -> str | None:
    settings = get_settings()
    token = settings.telegram_bot_token.strip()
    if not token:
        return None

    base = f"https://api.telegram.org/bot{token}"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            photos_resp = await client.get(
                f"{base}/getUserProfilePhotos",
                params={"user_id": telegram_id, "limit": 1},
            )
            photos_resp.raise_for_status()
            payload = photos_resp.json()
            if not payload.get("ok"):
                return None

            photos = (payload.get("result") or {}).get("photos") or []
            if not photos:
                return None

            file_id = photos[0][-1]["file_id"]
            file_resp = await client.get(f"{base}/getFile", params={"file_id": file_id})
            file_resp.raise_for_status()
            file_path = (file_resp.json().get("result") or {}).get("file_path")
            if not file_path:
                return None
            return f"https://api.telegram.org/file/bot{token}/{file_path}"
    except Exception:
        logger.warning("Failed to resolve Telegram avatar URL for %s", telegram_id, exc_info=True)
        return None


async def resolve_avatar_source_url(
    *,
    telegram_id: int,
    photo_url: str | None,
    init_photo_url: str | None = None,
) -> str | None:
    picked = pick_telegram_photo_url(init_photo_url, photo_url)
    if picked and is_telegram_cdn_url(picked):
        return picked
    if picked and not picked.startswith("/media/"):
        return picked
    return await _bot_profile_photo_url(telegram_id)


async def fetch_avatar_bytes(source_url: str) -> tuple[bytes, str]:
    async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
        resp = await client.get(source_url)
        resp.raise_for_status()
        content_type = (resp.headers.get("content-type") or "image/jpeg").split(";", 1)[0].lower()
        if "svg" in content_type or source_url.lower().endswith(".svg"):
            content_type = "image/svg+xml"
        return resp.content, content_type
