import uuid

import httpx
from aiogram import Bot

from app.providers.factory import get_storage_provider
from app.providers.storage.base import StorageBucket


async def upload_telegram_photo(bot: Bot, file_id: str, prefix: str = "arts") -> str:
    file = await bot.get_file(file_id)
    if not file.file_path:
        raise ValueError("Telegram file path missing")
    url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.content

    storage = get_storage_provider()
    key = f"{prefix}/{uuid.uuid4().hex}.jpg"
    result = await storage.upload(StorageBucket.PREVIEWS, key, data, "image/jpeg")
    return result.url
