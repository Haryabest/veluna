import logging
from uuid import UUID

from aiogram import Bot, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardMarkup

from app.bot.db import bot_session
from app.bot.filters import AdminFilter, is_bot_admin
from app.bot.keyboards import (
    ADMIN_MENU_TEXT_BROADCAST,
    ADMIN_MENU_TEXT_PRODUCTS,
    ADMIN_MENU_TEXT_PROMOS,
    ADMIN_MENU_TEXT_STATS,
    admin_main_menu,
    broadcast_confirm_kb,
    cancel_kb,
    main_reply_keyboard,
    product_item_menu,
    product_type_keyboard,
    products_menu,
    promo_item_menu,
    promos_menu,
    stats_submenu_keyboard,
)
from app.bot.states import AdminBroadcastStates, AdminProductStates, AdminPromoStates
from app.services.broadcast_service import BroadcastService
from app.bot.utils import upload_telegram_photo
from app.core.config import get_settings
from app.models import ShopProductType
from app.services.catalog_service import CatalogService

logger = logging.getLogger(__name__)

router = Router(name="admin")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


def _fmt_minutes(total_minutes: int) -> str:
    if total_minutes < 60:
        return f"{total_minutes} мин"
    hours, minutes = divmod(total_minutes, 60)
    if hours >= 24:
        days, hours = divmod(hours, 24)
        return f"{days} д {hours} ч {minutes} мин"
    return f"{hours} ч {minutes} мин"


def _admin_start_markup():
    settings = get_settings()
    url = settings.telegram_webapp_url
    if url.startswith("https://"):
        return main_reply_keyboard(url, include_admin=True)
    return admin_main_menu(url)


async def _reply_kb_for(user) -> ReplyKeyboardMarkup | None:
    settings = get_settings()
    url = settings.telegram_webapp_url
    if not url.startswith("https://"):
        return None
    return main_reply_keyboard(url, include_admin=await is_bot_admin(user))


def _admin_start_text() -> str:
    return (
        "Добро пожаловать в Veluna — AI-компаньоны в аниме-стиле.\n\n"
        "Кнопки управления всегда внизу экрана.\n\n"
        "<b>Администратор:</b> статистика, персонажи, рассылка, промокоды, товары."
    )


@router.message(Command("admin"), AdminFilter())
@router.callback_query(F.data == "adm:menu", AdminFilter())
async def admin_menu(event: Message | CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    text = _admin_start_text()
    markup = _admin_start_markup()
    if isinstance(event, CallbackQuery):
        await event.message.answer(text, reply_markup=markup)
        await event.answer()
    else:
        await event.answer(text, reply_markup=markup)


async def _stats_text() -> str:
    async with bot_session() as session:
        s = await CatalogService(session).user_stats()
    return (
        "<b>Статистика Veluna</b>\n\n"
        "<b>Пользователи</b>\n"
        f"• Зарегистрировано: <b>{s.total_users}</b>\n"
        f"• Пользовались сервисом (уник.): <b>{s.unique_users_ever}</b>\n"
        f"• Активны сейчас (24 ч): <b>{s.active_users_24h}</b>\n"
        f"• Активны (7 дней): <b>{s.active_users_7d}</b>\n"
        f"• Заблокировано: <b>{s.banned_users}</b>\n\n"
        "<b>Платежи</b>\n"
        f"• Успешных оплат: <b>{s.payments_count}</b>\n"
        f"• Куплено гемов: <b>{s.payments_gems_total}</b>\n"
        f"• Telegram Stars: <b>{s.payments_stars_total}</b>\n"
        f"• Доход (гемы, всего): <b>{s.revenue_gems_total}</b>\n\n"
        "<b>Расходы</b>\n"
        f"• Потрачено гемов: <b>{s.expenses_gems_total}</b>\n\n"
        "<b>Время пользования</b>\n"
        f"• Суммарно в чатах: <b>{_fmt_minutes(s.usage_time_minutes)}</b>\n"
        f"• В среднем на пользователя: <b>{_fmt_minutes(int(s.avg_usage_minutes_per_user))}</b>\n\n"
        "<b>Активность</b>\n"
        f"• Сообщений: <b>{s.total_messages}</b>\n"
        f"• Генераций: <b>{s.total_generations}</b>\n\n"
        "<b>Каталог</b>\n"
        f"• Промокодов (активных): <b>{s.active_promos}</b> / {s.total_promos}\n"
        f"• Товаров (активных): <b>{s.active_products}</b> / {s.total_products}"
    )


async def _send_stats(message: Message, user) -> None:
    settings = get_settings()
    kb = stats_submenu_keyboard(settings.telegram_webapp_url)
    try:
        text = await _stats_text()
        text += "\n\n<i>Кнопка «Пользователи» внизу — список, блокировка и редактирование.</i>"
    except Exception:
        text = (
            "<b>Статистика</b>\n\n"
            "Не удалось загрузить данные. Локально:\n"
            "<code>docker compose up postgres redis -d</code>\n"
            "<code>cd backend; .\\.venv\\Scripts\\alembic upgrade head</code>"
        )
    await message.answer(text, reply_markup=kb)
    logger.info("Admin stats keyboard sent (Пользователи submenu)")


@router.message(F.text == ADMIN_MENU_TEXT_STATS)
async def admin_stats_message(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _send_stats(message, message.from_user)


@router.callback_query(F.data == "adm:stats")
async def admin_stats(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await _send_stats(callback.message, callback.from_user)
    await callback.answer()


@router.message(F.text == ADMIN_MENU_TEXT_BROADCAST)
async def admin_broadcast_message(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AdminBroadcastStates.message)
    await message.answer(
        "<b>Рассылка</b>\n\nОтправьте текст сообщения для всех пользователей бота (HTML):",
        reply_markup=cancel_kb("adm:menu"),
    )


@router.callback_query(F.data == "adm:broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AdminBroadcastStates.message)
    await callback.message.answer(
        "<b>Рассылка</b>\n\nОтправьте текст сообщения (HTML):",
        reply_markup=cancel_kb("adm:menu"),
    )
    await callback.answer()


@router.message(AdminBroadcastStates.message)
async def admin_broadcast_preview(message: Message, state: FSMContext) -> None:
    text = (message.text or message.caption or "").strip()
    if not text:
        await message.answer("Текст не может быть пустым.")
        return
    await state.update_data(broadcast_text=text)
    await state.set_state(AdminBroadcastStates.confirm)
    preview = text if len(text) <= 500 else text[:500] + "…"
    await message.answer(
        f"<b>Предпросмотр рассылки</b>\n\n{preview}\n\nОтправить всем пользователям?",
        reply_markup=broadcast_confirm_kb(),
    )


@router.callback_query(AdminBroadcastStates.confirm, F.data == "adm:broadcast:cancel")
async def admin_broadcast_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Рассылка отменена.")
    await callback.answer()


@router.callback_query(AdminBroadcastStates.confirm, F.data == "adm:broadcast:confirm")
async def admin_broadcast_run(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    text = data.get("broadcast_text", "")
    await state.clear()
    await callback.message.edit_text("⏳ Рассылка запущена…")
    await callback.answer()

    admin_user_id = None
    async with bot_session() as session:
        from app.repositories.user_repository import UserRepository

        user = await UserRepository(session).get_by_telegram_id(callback.from_user.id)
        if user:
            admin_user_id = user.id
        record = await BroadcastService(session).send_broadcast(text, admin_id=admin_user_id)

    await callback.message.answer(
        "<b>Рассылка завершена</b>\n\n"
        f"Получателей: <b>{record.total_recipients}</b>\n"
        f"Доставлено: <b>{record.sent_count}</b>\n"
        f"Ошибок: <b>{record.failed_count}</b>",
        reply_markup=await _reply_kb_for(callback.from_user),
    )


# --- Promos ---
async def _send_promos_list(message: Message) -> None:
    async with bot_session() as session:
        promos = await CatalogService(session).list_promos()
    await message.answer("<b>Промокоды</b>", reply_markup=promos_menu(promos))


@router.message(F.text == ADMIN_MENU_TEXT_PROMOS)
async def admin_promos_list_message(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _send_promos_list(message)


@router.callback_query(F.data == "adm:promos")
async def admin_promos_list(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await _send_promos_list(callback.message)
    await callback.answer()


@router.callback_query(F.data == "adm:promo:add")
async def admin_promo_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminPromoStates.name)
    await callback.message.edit_text(
        "Создание промокода.\n\nВведите <b>название</b> (для админки):",
        reply_markup=cancel_kb("adm:promos"),
    )
    await callback.answer()


@router.message(AdminPromoStates.name)
async def admin_promo_name(message: Message, state: FSMContext) -> None:
    await state.update_data(promo_name=message.text.strip())
    await state.set_state(AdminPromoStates.discount)
    await message.answer(
        "Введите <b>скидку в %</b> (1–100):",
        reply_markup=cancel_kb("adm:promos"),
    )


@router.message(AdminPromoStates.discount)
async def admin_promo_discount(message: Message, state: FSMContext) -> None:
    try:
        discount = int(message.text.strip())
        if not 1 <= discount <= 100:
            raise ValueError
    except ValueError:
        await message.answer("Укажите число от 1 до 100.")
        return
    await state.update_data(discount_percent=discount)
    await state.set_state(AdminPromoStates.code)
    await message.answer(
        "Введите <b>код</b> промокода (латиница/цифры) или /auto для автогенерации:",
        reply_markup=cancel_kb("adm:promos"),
    )


@router.message(AdminPromoStates.code, Command("auto"))
async def admin_promo_code_auto(message: Message, state: FSMContext) -> None:
    await state.update_data(promo_code=None)
    await state.set_state(AdminPromoStates.max_uses)
    await message.answer(
        "Лимит использований (число) или /skip для безлимита:",
        reply_markup=cancel_kb("adm:promos"),
    )


@router.message(AdminPromoStates.code)
async def admin_promo_code(message: Message, state: FSMContext) -> None:
    await state.update_data(promo_code=message.text.strip())
    await state.set_state(AdminPromoStates.max_uses)
    await message.answer(
        "Лимит использований (число) или /skip для безлимита:",
        reply_markup=cancel_kb("adm:promos"),
    )


@router.message(AdminPromoStates.max_uses, Command("skip"))
async def admin_promo_max_skip(message: Message, state: FSMContext) -> None:
    await _create_promo(message, state, max_uses=None)


@router.message(AdminPromoStates.max_uses)
async def admin_promo_max(message: Message, state: FSMContext) -> None:
    try:
        max_uses = int(message.text.strip())
        if max_uses < 1:
            raise ValueError
    except ValueError:
        await message.answer("Введите целое число ≥ 1 или /skip.")
        return
    await _create_promo(message, state, max_uses=max_uses)


async def _create_promo(message: Message, state: FSMContext, max_uses: int | None) -> None:
    data = await state.get_data()
    try:
        async with bot_session() as session:
            promo = await CatalogService(session).create_promo(
                name=data["promo_name"],
                discount_percent=data["discount_percent"],
                code=data.get("promo_code"),
                max_uses=max_uses,
            )
    except ValueError as exc:
        await message.answer(str(exc))
        return
    await state.clear()
    limit = f"{promo.max_uses}" if promo.max_uses else "∞"
    await message.answer(
        f"Промокод создан:\n<b>{promo.code}</b> — {promo.name}, скидка {promo.discount_percent}%\n"
        f"Лимит: {limit}",
        reply_markup=promo_item_menu(str(promo.id), is_active=promo.is_active),
    )


@router.callback_query(F.data.startswith("adm:promo:view:"))
async def admin_promo_view(callback: CallbackQuery) -> None:
    promo_id = UUID(callback.data.split(":")[-1])
    async with bot_session() as session:
        promos = await CatalogService(session).list_promos()
    promo = next((p for p in promos if p.id == promo_id), None)
    if not promo:
        await callback.answer("Не найден", show_alert=True)
        return
    limit = f"{promo.max_uses}" if promo.max_uses else "∞"
    status = "активен" if promo.is_active else "выключен"
    await callback.message.edit_text(
        f"<b>{promo.name}</b>\nКод: <code>{promo.code}</code>\nСкидка: {promo.discount_percent}%\n"
        f"Статус: {status}\nИспользований: {promo.used_count} / {limit}",
        reply_markup=promo_item_menu(str(promo.id), is_active=promo.is_active),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm:promo:toggle:"))
async def admin_promo_toggle(callback: CallbackQuery) -> None:
    promo_id = UUID(callback.data.split(":")[-1])
    async with bot_session() as session:
        promo = await CatalogService(session).get_promo(promo_id)
        updated = await CatalogService(session).update_promo(promo_id, is_active=not promo.is_active)
    await callback.answer("Обновлено")
    limit = f"{updated.max_uses}" if updated.max_uses else "∞"
    status = "активен" if updated.is_active else "выключен"
    await callback.message.edit_text(
        f"<b>{updated.name}</b>\nКод: <code>{updated.code}</code>\nСкидка: {updated.discount_percent}%\n"
        f"Статус: {status}\nИспользований: {updated.used_count} / {limit}",
        reply_markup=promo_item_menu(str(updated.id), is_active=updated.is_active),
    )


@router.callback_query(F.data.startswith("adm:promo:max:"))
async def admin_promo_max_start(callback: CallbackQuery, state: FSMContext) -> None:
    promo_id = callback.data.split(":")[-1]
    await state.set_state(AdminPromoStates.edit_max_uses)
    await state.update_data(edit_promo_id=promo_id)
    await callback.message.edit_text(
        "Новый лимит использований (число) или /skip для безлимита:",
        reply_markup=cancel_kb(f"adm:promo:view:{promo_id}"),
    )
    await callback.answer()


@router.message(AdminPromoStates.edit_max_uses, Command("skip"))
async def admin_promo_max_clear(message: Message, state: FSMContext) -> None:
    await _save_promo_max(message, state, max_uses=None)


@router.message(AdminPromoStates.edit_max_uses)
async def admin_promo_max_save(message: Message, state: FSMContext) -> None:
    try:
        max_uses = int(message.text.strip())
        if max_uses < 1:
            raise ValueError
    except ValueError:
        await message.answer("Введите целое ≥ 1 или /skip.")
        return
    await _save_promo_max(message, state, max_uses=max_uses)


async def _save_promo_max(message: Message, state: FSMContext, max_uses: int | None) -> None:
    data = await state.get_data()
    promo_id = UUID(data["edit_promo_id"])
    async with bot_session() as session:
        promo = await CatalogService(session).update_promo(promo_id, max_uses=max_uses)
    await state.clear()
    limit = f"{promo.max_uses}" if promo.max_uses else "∞"
    await message.answer(
        f"Лимит обновлён: {limit}",
        reply_markup=promo_item_menu(str(promo.id), is_active=promo.is_active),
    )


@router.callback_query(F.data.startswith("adm:promo:del:"))
async def admin_promo_delete(callback: CallbackQuery, state: FSMContext) -> None:
    promo_id = UUID(callback.data.split(":")[-1])
    async with bot_session() as session:
        await CatalogService(session).delete_promo(promo_id)
    await callback.answer("Удалено")
    await admin_promos_list(callback, state)


# --- Products ---
async def _send_products_list(message: Message) -> None:
    async with bot_session() as session:
        products = await CatalogService(session).list_products()
    await message.answer("<b>Товары магазина</b>", reply_markup=products_menu(products))


@router.message(F.text == ADMIN_MENU_TEXT_PRODUCTS)
async def admin_products_list_message(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _send_products_list(message)


@router.callback_query(F.data == "adm:products")
async def admin_products_list(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await _send_products_list(callback.message)
    await callback.answer()


@router.callback_query(F.data == "adm:prod:add")
async def admin_product_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminProductStates.name)
    await callback.message.edit_text(
        "Создание товара.\n\nВведите <b>название</b>:",
        reply_markup=cancel_kb("adm:products"),
    )
    await callback.answer()


@router.message(AdminProductStates.name)
async def admin_product_name(message: Message, state: FSMContext) -> None:
    await state.update_data(product_name=message.text.strip())
    await state.set_state(AdminProductStates.product_type)
    await message.answer("Выберите <b>тип товара</b>:", reply_markup=product_type_keyboard())


@router.callback_query(AdminProductStates.product_type, F.data.startswith("adm:prod:type:"))
async def admin_product_type(callback: CallbackQuery, state: FSMContext) -> None:
    type_key = callback.data.split(":")[-1]
    mapping = {
        "gems": ShopProductType.GEMS,
        "credits": ShopProductType.CREDITS,
        "bundle": ShopProductType.BUNDLE,
    }
    await state.update_data(product_type=mapping[type_key].value)
    await state.set_state(AdminProductStates.price)
    await callback.message.edit_text(
        "Введите <b>цену</b> (целое число, в звёздах/гемах):",
        reply_markup=cancel_kb("adm:products"),
    )
    await callback.answer()


@router.message(AdminProductStates.price)
async def admin_product_price(message: Message, state: FSMContext) -> None:
    try:
        price = int(message.text.strip())
        if price < 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите неотрицательное целое число.")
        return
    await state.update_data(price=price)
    await state.set_state(AdminProductStates.sale_price)
    await message.answer(
        "Введите <b>цену со скидкой</b> или /skip если без скидки:",
        reply_markup=cancel_kb("adm:products"),
    )


@router.message(AdminProductStates.sale_price, Command("skip"))
async def admin_product_sale_skip(message: Message, state: FSMContext) -> None:
    await state.update_data(sale_price=None)
    await _ask_product_amounts(message, state)


@router.message(AdminProductStates.sale_price)
async def admin_product_sale(message: Message, state: FSMContext) -> None:
    try:
        sale = int(message.text.strip())
        if sale < 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите целое число или /skip.")
        return
    await state.update_data(sale_price=sale)
    await _ask_product_amounts(message, state)


async def _ask_product_amounts(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if data.get("product_type") == ShopProductType.GEMS.value:
        await state.set_state(AdminProductStates.gems_amount)
        await message.answer("Сколько <b>гемов</b> в пакете?", reply_markup=cancel_kb("adm:products"))
    elif data.get("product_type") == ShopProductType.CREDITS.value:
        await state.set_state(AdminProductStates.credits_amount)
        await message.answer("Сколько <b>кредитов</b> в пакете?", reply_markup=cancel_kb("adm:products"))
    else:
        await state.set_state(AdminProductStates.gems_amount)
        await message.answer(
            "Набор: введите количество <b>гемов</b> (далее спросим кредиты):",
            reply_markup=cancel_kb("adm:products"),
        )


@router.message(AdminProductStates.gems_amount)
async def admin_product_gems(message: Message, state: FSMContext) -> None:
    try:
        gems = int(message.text.strip())
    except ValueError:
        await message.answer("Введите целое число.")
        return
    await state.update_data(gems_amount=gems)
    data = await state.get_data()
    if data.get("product_type") == ShopProductType.BUNDLE.value:
        await state.set_state(AdminProductStates.credits_amount)
        await message.answer("Сколько <b>кредитов</b> в наборе?", reply_markup=cancel_kb("adm:products"))
    else:
        await _ask_product_photo(message, state)


@router.message(AdminProductStates.credits_amount)
async def admin_product_credits(message: Message, state: FSMContext) -> None:
    try:
        credits = int(message.text.strip())
    except ValueError:
        await message.answer("Введите целое число.")
        return
    await state.update_data(credits_amount=credits)
    await _ask_product_photo(message, state)


async def _ask_product_photo(message: Message, state: FSMContext) -> None:
    await state.set_state(AdminProductStates.photo)
    await message.answer(
        "Отправьте <b>фото товара</b> (или /skip):",
        reply_markup=cancel_kb("adm:products"),
    )


@router.message(AdminProductStates.photo, Command("skip"))
async def admin_product_photo_skip(message: Message, state: FSMContext) -> None:
    await _save_product(message, state, image_url=None)


@router.message(AdminProductStates.photo, F.photo)
async def admin_product_photo(message: Message, state: FSMContext, bot: Bot) -> None:
    try:
        image_url = await upload_telegram_photo(bot, message.photo[-1].file_id, prefix="products")
    except Exception as exc:
        await message.answer(f"Не удалось загрузить фото: {exc}")
        return
    await _save_product(message, state, image_url=image_url)


async def _save_product(message: Message, state: FSMContext, image_url: str | None = None) -> None:
    data = await state.get_data()
    if image_url is None and "product_image_url" in data:
        image_url = data.get("product_image_url")
    async with bot_session() as session:
        product = await CatalogService(session).create_product(
            name=data["product_name"],
            product_type=ShopProductType(data["product_type"]),
            price=data["price"],
            sale_price=data.get("sale_price"),
            gems_amount=data.get("gems_amount", 0),
            credits_amount=data.get("credits_amount", 0),
            image_url=image_url,
        )
    await state.clear()
    price_show = product.sale_price or product.price
    img = "\nФото: да" if product.image_url else "\nФото: нет"
    await message.answer(
        f"Товар создан: <b>{product.name}</b>\nТип: {product.product_type}\nЦена: {price_show}{img}",
        reply_markup=product_item_menu(str(product.id)),
    )


@router.callback_query(F.data.startswith("adm:prod:view:"))
async def admin_product_view(callback: CallbackQuery) -> None:
    product_id = UUID(callback.data.split(":")[-1])
    async with bot_session() as session:
        products = await CatalogService(session).list_products()
    product = next((p for p in products if p.id == product_id), None)
    if not product:
        await callback.answer("Не найден", show_alert=True)
        return
    sale = f"\nЦена со скидкой: {product.sale_price}" if product.sale_price else ""
    active = "в магазине" if product.is_active else "скрыт"
    img = f"\nФото: {product.image_url}" if product.image_url else "\nФото: нет"
    await callback.message.edit_text(
        f"<b>{product.name}</b>\nТип: {product.product_type}\nЦена: {product.price}{sale}\n"
        f"Гемы: {product.gems_amount} | Кредиты: {product.credits_amount}{img}\nСтатус: {active}",
        reply_markup=product_item_menu(str(product.id), is_active=product.is_active),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm:prod:edit:photo:"))
async def admin_product_edit_photo_start(callback: CallbackQuery, state: FSMContext) -> None:
    product_id = callback.data.split(":")[-1]
    await state.set_state(AdminProductStates.edit_photo)
    await state.update_data(edit_product_id=product_id)
    await callback.message.edit_text(
        "Отправьте новое <b>фото товара</b> (или /skip чтобы убрать):",
        reply_markup=cancel_kb(f"adm:prod:view:{product_id}"),
    )
    await callback.answer()


@router.message(AdminProductStates.edit_photo, Command("skip"))
async def admin_product_edit_photo_clear(message: Message, state: FSMContext) -> None:
    await _save_product_photo(message, state, image_url=None)


@router.message(AdminProductStates.edit_photo, F.photo)
async def admin_product_edit_photo_save(message: Message, state: FSMContext, bot: Bot) -> None:
    try:
        image_url = await upload_telegram_photo(bot, message.photo[-1].file_id, prefix="products")
    except Exception as exc:
        await message.answer(f"Ошибка загрузки: {exc}")
        return
    await _save_product_photo(message, state, image_url=image_url)


async def _save_product_photo(message: Message, state: FSMContext, image_url: str | None) -> None:
    data = await state.get_data()
    product_id = UUID(data["edit_product_id"])
    async with bot_session() as session:
        product = await CatalogService(session).update_product(product_id, image_url=image_url)
    await state.clear()
    await message.answer(
        "Фото товара обновлено." if image_url else "Фото удалено.",
        reply_markup=product_item_menu(str(product.id), is_active=product.is_active),
    )


@router.callback_query(F.data.startswith("adm:prod:toggle:"))
async def admin_product_toggle(callback: CallbackQuery) -> None:
    product_id = UUID(callback.data.split(":")[-1])
    async with bot_session() as session:
        product = await CatalogService(session).get_product(product_id)
        updated = await CatalogService(session).update_product(
            product_id, is_active=not product.is_active
        )
    await callback.answer("Обновлено")
    sale = f"\nЦена со скидкой: {updated.sale_price}" if updated.sale_price else ""
    active = "в магазине" if updated.is_active else "скрыт"
    await callback.message.edit_text(
        f"<b>{updated.name}</b>\nТип: {updated.product_type}\nЦена: {updated.price}{sale}\n"
        f"Гемы: {updated.gems_amount} | Кредиты: {updated.credits_amount}\nСтатус: {active}",
        reply_markup=product_item_menu(str(updated.id), is_active=updated.is_active),
    )


@router.callback_query(F.data.startswith("adm:prod:del:"))
async def admin_product_delete(callback: CallbackQuery, state: FSMContext) -> None:
    product_id = UUID(callback.data.split(":")[-1])
    async with bot_session() as session:
        await CatalogService(session).delete_product(product_id)
    await callback.answer("Удалено")
    await admin_products_list(callback, state)


@router.message(Command("cancel"), StateFilter("*"))
async def admin_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=_admin_start_markup())


from app.bot.handlers.admin_characters import router as admin_characters_router
from app.bot.handlers.admin_users import router as admin_users_router

router.include_router(admin_users_router)
router.include_router(admin_characters_router)
