from app.database.redis import redis_client

CATALOG_VERSION_KEY = "veluna:catalog:version"


async def get_catalog_version() -> int:
    try:
        raw = await redis_client.get(CATALOG_VERSION_KEY)
        return int(raw or 0)
    except Exception:
        return 0


async def bump_catalog_version() -> int:
    try:
        return int(await redis_client.incr(CATALOG_VERSION_KEY))
    except Exception:
        return 0
