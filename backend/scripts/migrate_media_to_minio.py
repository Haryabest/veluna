"""
Upload external image URLs from PostgreSQL into MinIO and rewrite URLs in DB.

Run inside backend container:
  docker exec veluna-backend python scripts/migrate_media_to_minio.py
"""
from __future__ import annotations

import asyncio
import logging
import mimetypes
import re
import uuid
from urllib.parse import urlparse

import httpx
from sqlalchemy import select, update

from app.core.config import get_settings
from app.database.session import async_session_factory
from app.models import Character, Generation, HomeArtItem, ShopProduct
from app.providers.factory import get_storage_provider
from app.providers.storage.base import StorageBucket

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("migrate_media")

EXTERNAL_HOSTS_SKIP_UPLOAD = frozenset()  # already in our bucket — handled separately


def _minio_public_base() -> str:
    return get_settings().minio_public_url.rstrip("/")


def _minio_internal_base() -> str:
    s = get_settings()
    scheme = "https" if s.minio_use_ssl else "http"
    return f"{scheme}://{s.minio_endpoint}/{s.minio_bucket}"


def is_external_url(url: str | None) -> bool:
    if not url or not url.startswith(("http://", "https://")):
        return False
    base = _minio_public_base()
    if url.startswith(base + "/") or url.startswith(base):
        return False
    internal = _minio_internal_base()
    if url.startswith(internal + "/") or url.startswith(internal):
        return False
    if "/veluna/" in url and "picsum.photos" not in url:
        return False
    return True


def normalize_existing_minio_url(url: str) -> str:
    """Rewrite localhost MinIO URLs to configured MINIO_PUBLIC_URL."""
    public = _minio_public_base()
    for prefix in (
        "http://localhost:9000/veluna",
        "http://127.0.0.1:9000/veluna",
        _minio_internal_base(),
    ):
        if url.startswith(prefix):
            path = url[len(prefix) :].lstrip("/")
            return f"{public}/{path}"
    return url


def resolve_fetch_url(url: str) -> str:
    """Use internal MinIO endpoint when fetching objects already in bucket."""
    internal = _minio_internal_base()
    public = _minio_public_base()
    if url.startswith(public):
        return url.replace(public, internal, 1)
    if url.startswith("http://localhost:9000/veluna"):
        return url.replace("http://localhost:9000/veluna", internal, 1)
    if url.startswith("http://127.0.0.1:9000/veluna"):
        return url.replace("http://127.0.0.1:9000/veluna", internal, 1)
    return url


def guess_content_type(url: str, data: bytes) -> str:
    ct, _ = mimetypes.guess_type(url)
    if ct and ct.startswith("image/"):
        return ct
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def file_extension(content_type: str) -> str:
    return {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}.get(
        content_type, "jpg"
    )


async def download_bytes(url: str) -> bytes:
    fetch_url = resolve_fetch_url(url)
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        response = await client.get(fetch_url)
        response.raise_for_status()
        return response.content


async def upload_image(
    bucket: StorageBucket,
    object_key: str,
    data: bytes,
    content_type: str,
) -> str:
    storage = get_storage_provider()
    result = await storage.upload(bucket, object_key, data, content_type)
    return result.url


async def migrate_url(
    url: str | None,
    *,
    bucket: StorageBucket,
    key_prefix: str,
    seed_hint: str,
) -> str | None:
    if not url:
        return None

    if not is_external_url(url):
        return normalize_existing_minio_url(url)

    logger.info("Migrating %s -> MinIO (%s)", url[:80], key_prefix)
    data = await download_bytes(url)
    content_type = guess_content_type(url, data)
    ext = file_extension(content_type)
    safe = re.sub(r"[^a-zA-Z0-9_-]", "-", seed_hint)[:48]
    object_key = f"{key_prefix}/{safe}-{uuid.uuid4().hex[:8]}.{ext}"
    return await upload_image(bucket, object_key, data, content_type)


async def placeholder_for_shop(name: str, product_type: str) -> str:
    seed = re.sub(r"\W+", "-", name.lower())[:30] or product_type
    url = f"https://picsum.photos/seed/veluna-shop-{seed}/400/400"
    data = await download_bytes(url)
    content_type = guess_content_type(url, data)
    ext = file_extension(content_type)
    object_key = f"shop/{seed}-{uuid.uuid4().hex[:8]}.{ext}"
    return await upload_image(StorageBucket.PREVIEWS, object_key, data, content_type)


async def run() -> None:
    settings = get_settings()
    logger.info("MinIO public URL: %s", settings.minio_public_url)
    stats = {"uploaded": 0, "normalized": 0, "skipped": 0, "errors": 0}

    async with async_session_factory() as session:
        # Characters
        result = await session.execute(select(Character))
        for ch in result.scalars().all():
            try:
                new_preview = await migrate_url(
                    ch.preview_url,
                    bucket=StorageBucket.CHARACTERS,
                    key_prefix=ch.slug,
                    seed_hint=f"{ch.slug}-preview",
                )
                new_avatar = await migrate_url(
                    ch.avatar_url,
                    bucket=StorageBucket.CHARACTERS,
                    key_prefix=ch.slug,
                    seed_hint=f"{ch.slug}-avatar",
                )
                if not new_avatar and new_preview:
                    new_avatar = new_preview

                changed = False
                if new_preview and new_preview != ch.preview_url:
                    ch.preview_url = new_preview
                    changed = True
                    stats["uploaded"] += 1
                if new_avatar and new_avatar != ch.avatar_url:
                    ch.avatar_url = new_avatar
                    changed = True
                elif new_preview and not ch.avatar_url:
                    ch.avatar_url = new_preview
                    changed = True

                if not changed and ch.preview_url:
                    norm = normalize_existing_minio_url(ch.preview_url)
                    if norm != ch.preview_url:
                        ch.preview_url = norm
                        ch.avatar_url = ch.avatar_url and normalize_existing_minio_url(ch.avatar_url)
                        stats["normalized"] += 1
                        changed = True

                if not changed:
                    stats["skipped"] += 1
            except Exception as exc:
                logger.error("Character %s: %s", ch.slug, exc)
                stats["errors"] += 1

        # Shop products without image
        result = await session.execute(select(ShopProduct))
        for product in result.scalars().all():
            try:
                if product.image_url and not is_external_url(product.image_url):
                    norm = normalize_existing_minio_url(product.image_url)
                    if norm != product.image_url:
                        product.image_url = norm
                        stats["normalized"] += 1
                    else:
                        stats["skipped"] += 1
                    continue

                if product.image_url and is_external_url(product.image_url):
                    new_url = await migrate_url(
                        product.image_url,
                        bucket=StorageBucket.PREVIEWS,
                        key_prefix="shop",
                        seed_hint=product.name,
                    )
                else:
                    logger.info("Placeholder image for shop product: %s", product.name)
                    ptype = getattr(product.product_type, "value", str(product.product_type))
                    new_url = await placeholder_for_shop(product.name, ptype)

                product.image_url = new_url
                stats["uploaded"] += 1
            except Exception as exc:
                logger.error("Shop product %s: %s", product.name, exc)
                stats["errors"] += 1

        # Home art items
        result = await session.execute(select(HomeArtItem))
        for art in result.scalars().all():
            try:
                if not art.image_url:
                    stats["skipped"] += 1
                    continue
                if not is_external_url(art.image_url):
                    norm = normalize_existing_minio_url(art.image_url)
                    if norm != art.image_url:
                        art.image_url = norm
                        stats["normalized"] += 1
                    else:
                        stats["skipped"] += 1
                    continue
                art.image_url = await migrate_url(
                    art.image_url,
                    bucket=StorageBucket.PREVIEWS,
                    key_prefix="home-arts",
                    seed_hint=art.title or "art",
                )
                stats["uploaded"] += 1
            except Exception as exc:
                logger.error("Home art %s: %s", art.id, exc)
                stats["errors"] += 1

        # Generations with external image URLs
        result = await session.execute(
            select(Generation).where(Generation.image_url.isnot(None))
        )
        for gen in result.scalars().all():
            try:
                for field in ("image_url", "thumbnail_url"):
                    current = getattr(gen, field)
                    if not current or not is_external_url(current):
                        if current:
                            norm = normalize_existing_minio_url(current)
                            if norm != current:
                                setattr(gen, field, norm)
                                stats["normalized"] += 1
                        continue
                    new_url = await migrate_url(
                        current,
                        bucket=StorageBucket.GENERATIONS,
                        key_prefix=str(gen.user_id),
                        seed_hint=f"gen-{field}",
                    )
                    setattr(gen, field, new_url)
                    stats["uploaded"] += 1
            except Exception as exc:
                logger.error("Generation %s: %s", gen.id, exc)
                stats["errors"] += 1

        await session.commit()

    logger.info("Done: %s", stats)


if __name__ == "__main__":
    asyncio.run(run())
