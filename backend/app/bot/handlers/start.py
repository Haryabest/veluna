from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.bot.filters import _is_admin_user
from app.bot.keyboards import start_keyboard
from app.core.config import get_settings

router = Router(name="start")


def _start_text(is_admin: bool) -> str:
    lines = [
        "Добро пожаловать в Veluna — AI-компаньоны в аниме-стиле.",
        "",
        "Нажмите «Открыть Veluna», чтобы запустить приложение.",
    ]
    if is_admin:
        lines.extend(
            [
                "",
                "<b>Администратор</b> — ниже кнопки управления:",
                "статистика, рассылка, арт на главной, промокоды, товары.",
            ]
        )
    return "\n".join(lines)


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
async def cmd_admin_denied(message: Message) -> None:
    if not _is_admin_user(message.from_user):
        await message.answer("Доступ только для администратора. Отправьте /id чтобы узнать свой username.")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    settings = get_settings()
    webapp_url = settings.telegram_webapp_url
    is_admin = _is_admin_user(message.from_user)

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

    await message.answer(
        _start_text(is_admin),
        reply_markup=start_keyboard(webapp_url, include_admin=is_admin),
    )
