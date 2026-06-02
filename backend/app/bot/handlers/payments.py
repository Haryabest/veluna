import logging
from uuid import UUID

from aiogram import F, Router
from aiogram.types import Message, PreCheckoutQuery

from app.bot.db import bot_session
from app.services.shop_service import ShopService

logger = logging.getLogger(__name__)
router = Router(name="payments")


@router.pre_checkout_query()
async def pre_checkout_handler(query: PreCheckoutQuery) -> None:
    async with bot_session() as session:
        ok = await ShopService(session).approve_pre_checkout(query.invoice_payload)
    if ok:
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Заказ не найден или уже оплачен")


@router.message(F.successful_payment)
async def successful_payment_handler(message: Message) -> None:
    payment = message.successful_payment
    if not payment or not payment.invoice_payload.startswith("purchase:"):
        return

    try:
        purchase_id = UUID(payment.invoice_payload.split(":", 1)[1])
    except ValueError:
        logger.warning("Invalid purchase payload: %s", payment.invoice_payload)
        return

    async with bot_session() as session:
        service = ShopService(session)
        await service.complete_purchase(purchase_id, payment.telegram_payment_charge_id)

    await message.answer("✅ Оплата прошла успешно! Гемы зачислены на баланс.")
