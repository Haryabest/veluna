"""Rewrite MinIO absolute URLs to /media/... for same-origin access via Pinggy tunnel."""
from __future__ import annotations

import asyncio
import re

from sqlalchemy import select, text

from app.database.session import async_session_factory
from app.models import Character, Generation, HomeArtItem, ShopProduct

PREFIXES = (
    "http://localhost:9000/veluna/",
    "http://127.0.0.1:9000/veluna/",
    "https://localhost:9000/veluna/",
)


def to_relative(url: str | None) -> str | None:
    if not url:
        return None
    for p in PREFIXES:
        if url.startswith(p):
            return "/media/" + url[len(p) :]
    if url.startswith("/media/"):
        return url
    m = re.match(r"https?://[^/]+/veluna/(.+)", url)
    if m:
        return f"/media/{m.group(1)}"
    return url


async def run() -> None:
    async with async_session_factory() as session:
        for model, fields in (
            (Character, ("avatar_url", "preview_url")),
            (ShopProduct, ("image_url",)),
            (HomeArtItem, ("image_url",)),
            (Generation, ("image_url", "thumbnail_url")),
        ):
            result = await session.execute(select(model))
            for row in result.scalars().all():
                for field in fields:
                    old = getattr(row, field)
                    new = to_relative(old)
                    if new != old:
                        setattr(row, field, new)
        await session.commit()
    print("Media URLs updated to /media/... paths")


if __name__ == "__main__":
    asyncio.run(run())
