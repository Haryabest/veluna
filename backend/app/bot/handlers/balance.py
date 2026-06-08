from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.db import bot_session
from app.bot.finance_display import format_user_finance_stats
from app.bot.keyboards import user_finance_keyboard
from app.repositories.generation_repository import PaymentRepository
from app.repositories.user_repository import UserRepository

router = Router(name="balance")

USER_FINANCE_CB = "user:finance"


async def _reply_finance(target: Message) -> None:
    telegram_id = target.from_user.id
    async with bot_session() as session:
        user = await UserRepository(session).get_by_telegram_id(telegram_id)
        if not user:
            await target.answer(
                "Сначала откройте Veluna через /start — так мы создадим ваш аккаунт."
            )
            return
        stats = await PaymentRepository(session).get_finance_stats(user.id)

    await target.answer(
        format_user_finance_stats(stats),
        reply_markup=user_finance_keyboard(),
    )


@router.message(Command("balance", "stats", "баланс"))
async def cmd_balance(message: Message) -> None:
    await _reply_finance(message)


@router.callback_query(F.data == USER_FINANCE_CB)
async def cb_balance(callback: CallbackQuery) -> None:
    if callback.message:
        await _reply_finance(callback.message)
    await callback.answer()
