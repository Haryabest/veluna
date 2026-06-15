from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot.db import bot_session
from app.bot.filters import is_bot_admin
from app.bot.i18n import t, user_locale
from app.bot.menu import sync_user_menu_button
from app.bot.keyboards import (
    language_choice_inline,
    main_reply_keyboard,
    user_start_inline,
)
from app.repositories.user_repository import UserRepository
from app.utils.locale import normalize_app_locale

router = Router(name="locale")

LANG_CB_PREFIX = "lang:"
SWITCH_LANGUAGE_TEXTS = frozenset(
    {
        "🌐 Переключить язык",
        "🌐 Switch language",
    }
)


async def _save_locale(telegram_id: int, locale: str):
    async with bot_session() as session:
        repo = UserRepository(session)
        user = await repo.get_by_telegram_id(telegram_id)
        if not user:
            return None
        await repo.update(
            user,
            language_code=normalize_app_locale(locale),
            locale_selected=True,
        )
        return user


@router.callback_query(F.data.startswith(LANG_CB_PREFIX))
async def on_language_chosen(callback: CallbackQuery) -> None:
    locale = callback.data.removeprefix(LANG_CB_PREFIX)
    if locale not in ("ru", "en"):
        await callback.answer("Unknown language")
        return

    user = await _save_locale(callback.from_user.id, locale)
    if not user:
        await callback.answer("User not found")
        return

    from app.core.config import reload_settings

    settings = reload_settings()
    webapp_url = (settings.telegram_webapp_url or "").rstrip("/")

    saved_key = "language_saved" if locale == "ru" else "language_saved_en"
    await callback.message.edit_text(t(saved_key, locale))
    is_admin = await is_bot_admin(callback.from_user)
    if webapp_url.startswith("https://"):
        await callback.message.answer(
            t("welcome", locale),
            reply_markup=user_start_inline(webapp_url, locale),
        )
    await callback.message.answer(
        t("menu_hint", locale),
        reply_markup=main_reply_keyboard(webapp_url, locale, include_admin=is_admin),
    )
    if webapp_url.startswith("https://"):
        await sync_user_menu_button(callback.bot, callback.from_user.id, locale, webapp_url)
    await callback.answer()


@router.message(F.text.in_(SWITCH_LANGUAGE_TEXTS))
async def on_switch_language(message: Message) -> None:
    async with bot_session() as session:
        repo = UserRepository(session)
        user = await repo.get_by_telegram_id(message.from_user.id)
        loc = user_locale(user)
    await message.answer(
        t("choose_language", loc),
        reply_markup=language_choice_inline(),
    )
