from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.bot.filters import is_bot_admin
from app.bot.keyboards import start_keyboard
from app.core.config import reload_settings

router = Router(name="start")


def _start_text(is_admin: bool, webapp_url: str) -> str:
    lines = [
        "Добро пожаловать в Veluna — AI-компаньоны в аниме-стиле.",
        "",
        "⚠️ Старые ссылки <b>xijlo-…pinggy-free.link</b> больше не работают.",
        "Открывайте Mini App через синюю кнопку меню Telegram «Открыть Veluna».",
        "",
        f"Актуальный адрес: <code>{webapp_url.rstrip('/')}</code>",
    ]
    if is_admin:
        lines.extend(
            [
                "",
                "<b>Администратор</b> — кнопки управления всегда внизу:",
                "статистика, создание персонажей, рассылка, промокоды, товары.",
            ]
        )
    return "\n".join(lines)


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

    await message.answer(_admin_start_text(), reply_markup=_admin_start_markup())


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    settings = reload_settings()
    webapp_url = settings.telegram_webapp_url
    is_admin = await is_bot_admin(message.from_user)

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
    await message.answer(
        _start_text(is_admin, url),
        reply_markup=start_keyboard(url, include_admin=is_admin),
    )


@router.message(Command("open"))
async def cmd_open(message: Message) -> None:
    """Refresh Web App link (use if an old tunnel URL opens)."""
    settings = reload_settings()
    webapp_url = (settings.telegram_webapp_url or "").rstrip("/")
    if not webapp_url.startswith("https://"):
        await message.answer("Mini App URL не настроен. Запустите туннель: dev-miniapp-up.ps1")
        return
    await message.answer(
        "Mini App открывается через синюю кнопку меню Telegram «Открыть Veluna».\n\n"
        f"Актуальный адрес:\n<code>{webapp_url}</code>",
    )
