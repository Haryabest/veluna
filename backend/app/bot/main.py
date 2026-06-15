import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import MenuButtonWebApp, WebAppInfo

from app.bot.handlers import admin_router, balance_router, locale_router, payments_router, start_router
from app.core.config import get_settings, reload_settings

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)


async def _set_menu_webapp(bot: Bot, webapp_url: str, locale: str = "en") -> None:
    if not webapp_url.startswith("https://"):
        logger.warning("Menu Web App skipped: Telegram requires HTTPS (got %s)", webapp_url)
        return
    from app.bot.i18n import t

    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text=t("open_veluna", locale),
                web_app=WebAppInfo(url=webapp_url),
            ),
        )
    except (TelegramBadRequest, TelegramNetworkError) as exc:
        logger.warning("Menu Web App not set: %s", exc)


async def _wait_for_telegram_api(bot: Bot, retries: int = 12, delay: float = 5.0) -> None:
    """Retry when api.telegram.org is blocked (VPN/firewall on Windows host)."""
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            me = await bot.get_me()
            logger.info("Connected to Telegram as @%s", me.username)
            return
        except TelegramNetworkError as exc:
            last_exc = exc
            logger.warning(
                "Telegram API unreachable (attempt %s/%s): %s",
                attempt,
                retries,
                exc,
            )
            if attempt < retries:
                await asyncio.sleep(delay)
    if last_exc:
        raise last_exc
    raise RuntimeError("api.telegram.org unreachable")


async def _watch_tunnel_url(bot: Bot, interval: float = 20.0) -> None:
    """Re-read .env when dev-miniapp-up.ps1 changes TELEGRAM_WEBAPP_URL."""
    last_url = ""
    while True:
        await asyncio.sleep(interval)
        settings = reload_settings()
        url = settings.telegram_webapp_url
        if url and url.startswith("https://") and url != last_url:
            await _set_menu_webapp(bot, url)
            last_url = url
            logger.info("Mini App URL synced: %s", url)


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
    dp.include_router(locale_router)
    dp.include_router(start_router)
    dp.include_router(balance_router)
    dp.include_router(payments_router)
    dp.include_router(admin_router)

    await _wait_for_telegram_api(bot)

    if settings.telegram_webapp_url:
        await _set_menu_webapp(bot, settings.telegram_webapp_url, locale="en")

    if not settings.is_production:
        asyncio.create_task(_watch_tunnel_url(bot))

    logger.info("Veluna Telegram bot started (polling)")
    await dp.start_polling(bot, handle_signals=False)


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
