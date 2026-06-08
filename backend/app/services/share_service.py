import logging

from aiogram import Bot
from aiogram.types import InlineQueryResultPhoto

from app.core.config import get_settings
from app.core.exceptions import ServiceUnavailableError, ValidationError

logger = logging.getLogger(__name__)

SHARE_CAPTION_TEMPLATE = "Смотри какой арт!\n\n{bot_link}"


async def prepare_generation_share(
    *,
    telegram_user_id: int,
    image_url: str,
) -> tuple[str, str]:
    """Save a prepared inline photo message for Telegram WebApp shareMessage."""
    settings = get_settings()
    if not settings.telegram_bot_token.strip():
        raise ServiceUnavailableError("Бот не настроен")
    if not image_url.strip():
        raise ValidationError("Нет изображения для отправки")

    bot_link = settings.telegram_bot_link
    caption = (
        SHARE_CAPTION_TEMPLATE.format(bot_link=bot_link)
        if bot_link
        else "Смотри какой арт!"
    )

    bot = Bot(token=settings.telegram_bot_token)
    try:
        prepared = await bot.save_prepared_inline_message(
            user_id=telegram_user_id,
            result=InlineQueryResultPhoto(
                id="veluna-art",
                photo_url=image_url,
                title="Veluna",
                caption=caption[:1024],
            ),
            allow_user_chats=True,
            allow_bot_chats=False,
            allow_group_chats=True,
            allow_channel_chats=False,
        )
        return prepared.id, bot_link
    except Exception as exc:
        logger.exception("prepare_generation_share failed for user %s", telegram_user_id)
        raise ServiceUnavailableError("Не удалось подготовить сообщение для Telegram") from exc
    finally:
        await bot.session.close()
