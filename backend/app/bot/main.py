import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import MenuButtonWebApp, WebAppInfo

from app.bot.handlers import admin_router, start_router
from app.core.config import get_settings

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)


async def _set_menu_webapp(bot: Bot, webapp_url: str) -> None:
    if not webapp_url.startswith("https://"):
        logger.warning("Menu Web App skipped: Telegram requires HTTPS (got %s)", webapp_url)
        return
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="Veluna", web_app=WebAppInfo(url=webapp_url)),
        )
    except TelegramBadRequest as exc:
        logger.warning("Menu Web App not set: %s", exc)


async def run_bot() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN is not set")
        sys.exit(1)
    if not settings.telegram_webapp_url:
        logger.warning("TELEGRAM_WEBAPP_URL is not set — /start will show a setup message")

    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start_router)
    dp.include_router(admin_router)

    if settings.telegram_webapp_url:
        await _set_menu_webapp(bot, settings.telegram_webapp_url)

    logger.info("Veluna Telegram bot started (polling)")
    await dp.start_polling(bot)


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
