"""Per-user Telegram menu button (Mini App) with correct locale text."""

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.types import MenuButtonWebApp, WebAppInfo

from app.bot.i18n import t

logger = logging.getLogger(__name__)


async def sync_user_menu_button(bot: Bot, telegram_id: int, locale: str, webapp_url: str) -> None:
    if not webapp_url.startswith("https://"):
        return
    try:
        await bot.set_chat_menu_button(
            chat_id=telegram_id,
            menu_button=MenuButtonWebApp(
                text=t("open_veluna", locale),
                web_app=WebAppInfo(url=webapp_url.rstrip("/")),
            ),
        )
    except (TelegramBadRequest, TelegramNetworkError) as exc:
        logger.warning("Menu button not set for %s: %s", telegram_id, exc)
