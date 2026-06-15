from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.bot.db import bot_session
from app.bot.filters import is_bot_admin
from app.bot.i18n import t, user_locale
from app.bot.keyboards import (
    language_choice_inline,
    main_reply_keyboard,
    user_start_inline,
)
from app.core.config import reload_settings
from app.repositories.user_repository import UserRepository
from app.services.user_ban_service import format_ban_message, is_ban_active, refresh_ban_status
from app.utils.locale import locale_from_telegram
from app.bot.menu import sync_user_menu_button

router = Router(name="start")


async def _ensure_user(message: Message):
    tg = message.from_user
    async with bot_session() as session:
        repo = UserRepository(session)
        user = await repo.get_by_telegram_id(tg.id)
        if not user:
            user = await repo.create(
                telegram_id=tg.id,
                username=tg.username,
                first_name=tg.first_name,
                last_name=tg.last_name,
                language_code=locale_from_telegram(tg.language_code),
                locale_selected=False,
            )
        return user


@router.message(Command("paysupport"))
async def cmd_paysupport(message: Message) -> None:
    await message.answer(
        "Поддержка по оплатам Veluna:\n"
        "• Оплата только Telegram Stars (⭐) внутри бота.\n"
        "• Если видите PROVIDER_ACCOUNT_INVALID — откройте Mini App "
        "с телефона (Android/iOS), не с ПК.\n"
        "• В @BotFather у бота не должно быть подключённых "
        "карточных провайдеров (Stripe/ЮKassa) — только Stars.\n"
        "• Напишите @Iabobuss или ответьте на это сообщение с описанием проблемы."
    )


@router.message(Command("terms"))
async def cmd_terms(message: Message) -> None:
    await message.answer(
        "Условия Veluna: цифровые товары (гемы/кредиты), оплата Stars, "
        "возврат — через /paysupport в течение 24 ч после покупки."
    )


@router.message(Command("id"))
async def cmd_id(message: Message) -> None:
    user = message.from_user
    uname = f"@{user.username}" if user.username else "(username не задан в Telegram)"
    await message.answer(
        f"Ваш Telegram ID: <code>{user.id}</code>\n"
        f"Username: {uname}\n\n"
        "Для админки добавьте в .env:\n"
        f"<code>ADMIN_TELEGRAM_USERNAMES={user.username or 'ваш_username'}</code>"
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if not await is_bot_admin(message.from_user):
        await message.answer("Доступ только для администратора. Отправьте /id чтобы узнать свой username.")
        return
    from app.bot.handlers.admin import _admin_start_markup, _admin_start_text

    async with bot_session() as session:
        db_user = await UserRepository(session).get_by_telegram_id(message.from_user.id)
    loc = user_locale(db_user)
    await message.answer(_admin_start_text(), reply_markup=_admin_start_markup(loc))


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    settings = reload_settings()
    webapp_url = settings.telegram_webapp_url
    is_admin = await is_bot_admin(message.from_user)

    user = await _ensure_user(message)
    async with bot_session() as session:
        repo = UserRepository(session)
        user = await repo.get_by_telegram_id(message.from_user.id)
        if user:
            user = await refresh_ban_status(user, repo)
            if is_ban_active(user):
                await message.answer(format_ban_message(user.ban_reason, user.banned_until))
                return

    if not webapp_url:
        await message.answer(
            "Veluna пока не настроена: укажите TELEGRAM_WEBAPP_URL в .env."
        )
        return
    if not webapp_url.startswith("https://"):
        await message.answer(
            "Veluna запущена, но Mini App ещё не доступна.\n\n"
            "Укажите в .env TELEGRAM_WEBAPP_URL с HTTPS.\n\n"
            f"Сейчас: {webapp_url}"
        )
        return

    url = webapp_url.rstrip("/")
    loc = user_locale(user)

    if user and not user.locale_selected:
        await message.answer(
            t("choose_language", loc),
            reply_markup=language_choice_inline(),
        )
        return

    await message.answer(
        t("welcome", loc),
        reply_markup=user_start_inline(url, loc),
    )
    await message.answer(
        t("menu_hint", loc),
        reply_markup=main_reply_keyboard(url, loc, include_admin=is_admin),
    )
    await sync_user_menu_button(message.bot, message.from_user.id, loc, url)


@router.message(Command("open"))
async def cmd_open(message: Message) -> None:
    """Refresh Web App link (use if an old tunnel URL opens)."""
    settings = reload_settings()
    webapp_url = (settings.telegram_webapp_url or "").rstrip("/")
    if not webapp_url.startswith("https://"):
        await message.answer("Mini App URL не настроен. Запустите туннель: dev-miniapp-up.ps1")
        return
    user = await _ensure_user(message)
    loc = user_locale(user)
    await message.answer(t("welcome", loc), reply_markup=user_start_inline(webapp_url, loc))
    await sync_user_menu_button(message.bot, message.from_user.id, loc, webapp_url)
