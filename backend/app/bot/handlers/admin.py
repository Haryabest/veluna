from uuid import UUID

from aiogram import Bot, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardMarkup

from app.bot.db import bot_session
from app.bot.filters import AdminFilter, _is_admin_user
from app.bot.keyboards import (
    ADMIN_MENU_TEXT_ARTS,
    ADMIN_MENU_TEXT_BROADCAST,
    ADMIN_MENU_TEXT_PRODUCTS,
    ADMIN_MENU_TEXT_PROMOS,
    ADMIN_MENU_TEXT_STATS,
    admin_main_menu,
    art_item_menu,
    arts_menu,
    cancel_kb,
    main_reply_keyboard,
    product_item_menu,
    product_type_keyboard,
    products_menu,
    promo_item_menu,
    promos_menu,
)
from app.bot.states import AdminArtStates, AdminProductStates, AdminPromoStates
from app.bot.utils import upload_telegram_photo
from app.core.config import get_settings
from app.models import ShopProductType
from app.services.catalog_service import CatalogService

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


def _reply_kb_for(user) -> ReplyKeyboardMarkup | None:
    settings = get_settings()
    url = settings.telegram_webapp_url
    if not url.startswith("https://"):
        return None
    return main_reply_keyboard(url, include_admin=_is_admin_user(user))


def _admin_start_text() -> str:
    return (
        "Добро пожаловать в Veluna — AI-компаньоны в аниме-стиле.\n\n"
        "Кнопки управления всегда внизу экрана.\n\n"
        "<b>Администратор:</b> статистика, рассылка, арт, промокоды, товары."
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
        f"• Генераций: <b>{s.total_generations}</b>"
    )


async def _send_stats(message: Message, user) -> None:
    kb = _reply_kb_for(user)
    try:
        text = await _stats_text()
    except Exception:
        text = (
            "<b>Статистика</b>\n\n"
            "Не удалось загрузить данные. Проверьте миграции БД:\n"
            "<code>docker exec veluna-backend alembic upgrade head</code>"
        )
    await message.answer(text, reply_markup=kb)


@router.message(F.text == ADMIN_MENU_TEXT_STATS)
async def admin_stats_message(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _send_stats(message, message.from_user)


@router.callback_query(F.data == "adm:stats")
async def admin_stats(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await _send_stats(callback.message, callback.from_user)
    await callback.answer()


def _broadcast_text() -> str:
    return (
        "<b>Рассылка</b>\n\n"
        "Раздел в разработке. Здесь будет массовая отправка сообщений всем пользователям бота."
    )


@router.message(F.text == ADMIN_MENU_TEXT_BROADCAST)
async def admin_broadcast_message(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(_broadcast_text(), reply_markup=_reply_kb_for(message.from_user))


@router.callback_query(F.data == "adm:broadcast")
async def admin_broadcast_stub(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer(_broadcast_text(), reply_markup=_reply_kb_for(callback.from_user))
    await callback.answer()


# --- Home art ---
async def _send_arts_list(message: Message) -> None:
    async with bot_session() as session:
        items = await CatalogService(session).list_home_arts()
    text = "<b>Арт-объекты на главной</b>\n\nВыберите объект или добавьте новый."
    if not items:
        text += "\n\n<i>Список пуст.</i>"
    await message.answer(text, reply_markup=arts_menu(items))


@router.message(F.text == ADMIN_MENU_TEXT_ARTS)
async def admin_arts_list_message(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _send_arts_list(message)


@router.callback_query(F.data == "adm:arts")
async def admin_arts_list(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await _send_arts_list(callback.message)
    await callback.answer()


@router.callback_query(F.data == "adm:art:add")
async def admin_art_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminArtStates.title)
    await callback.message.edit_text(
        "Создание арт-объекта.\n\nВведите <b>название</b>:",
        reply_markup=cancel_kb("adm:arts"),
    )
    await callback.answer()


@router.message(AdminArtStates.title)
async def admin_art_add_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text.strip())
    await state.set_state(AdminArtStates.description)
    await message.answer("Введите <b>описание</b>:", reply_markup=cancel_kb("adm:arts"))


@router.message(AdminArtStates.description)
async def admin_art_add_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text.strip())
    await state.set_state(AdminArtStates.photo)
    await message.answer(
        "Отправьте <b>фото</b> (или /skip чтобы без фото):",
        reply_markup=cancel_kb("adm:arts"),
    )


@router.message(AdminArtStates.photo, Command("skip"))
async def admin_art_add_skip_photo(message: Message, state: FSMContext) -> None:
    await _save_new_art(message, state, image_url=None)


@router.message(AdminArtStates.photo, F.photo)
async def admin_art_add_photo(message: Message, state: FSMContext, bot: Bot) -> None:
    photo = message.photo[-1]
    try:
        image_url = await upload_telegram_photo(bot, photo.file_id)
    except Exception as exc:
        await message.answer(f"Не удалось загрузить фото: {exc}")
        return
    await _save_new_art(message, state, image_url=image_url)


async def _save_new_art(message: Message, state: FSMContext, image_url: str | None) -> None:
    data = await state.get_data()
    async with bot_session() as session:
        item = await CatalogService(session).create_home_art(
            title=data["title"],
            description=data["description"],
            image_url=image_url,
        )
    await state.clear()
    await message.answer(
        f"Арт «<b>{item.title}</b>» создан.",
        reply_markup=art_item_menu(str(item.id)),
    )


@router.callback_query(F.data.startswith("adm:art:view:"))
async def admin_art_view(callback: CallbackQuery) -> None:
    item_id = UUID(callback.data.split(":")[-1])
    async with bot_session() as session:
        items = await CatalogService(session).list_home_arts()
    item = next((i for i in items if i.id == item_id), None)
    if not item:
        await callback.answer("Не найден", show_alert=True)
        return
    photo_line = f"\nФото: {item.image_url}" if item.image_url else "\nФото: нет"
    await callback.message.edit_text(
        f"<b>{item.title}</b>\n\n{item.description}{photo_line}",
        reply_markup=art_item_menu(str(item.id)),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm:art:del:"))
async def admin_art_delete_fixed(callback: CallbackQuery, state: FSMContext) -> None:
    item_id = UUID(callback.data.split(":")[-1])
    async with bot_session() as session:
        await CatalogService(session).delete_home_art(item_id)
    await callback.answer("Удалено")
    await state.clear()
    async with bot_session() as session:
        items = await CatalogService(session).list_home_arts()
    await callback.message.edit_text(
        "<b>Арт-объекты на главной</b>\n\nОбъект удалён.",
        reply_markup=arts_menu(items),
    )


@router.callback_query(F.data.startswith("adm:art:edit:title:"))
async def admin_art_edit_title_start(callback: CallbackQuery, state: FSMContext) -> None:
    item_id = callback.data.split(":")[-1]
    await state.set_state(AdminArtStates.edit_title)
    await state.update_data(edit_art_id=item_id)
    await callback.message.edit_text(
        "Введите новое <b>название</b>:",
        reply_markup=cancel_kb(f"adm:art:view:{item_id}"),
    )
    await callback.answer()


@router.message(AdminArtStates.edit_title)
async def admin_art_edit_title_save(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    item_id = UUID(data["edit_art_id"])
    async with bot_session() as session:
        item = await CatalogService(session).update_home_art(item_id, title=message.text.strip())
    await state.clear()
    await message.answer(f"Название обновлено: <b>{item.title}</b>", reply_markup=art_item_menu(str(item.id)))


@router.callback_query(F.data.startswith("adm:art:edit:desc:"))
async def admin_art_edit_desc_start(callback: CallbackQuery, state: FSMContext) -> None:
    item_id = callback.data.split(":")[-1]
    await state.set_state(AdminArtStates.edit_description)
    await state.update_data(edit_art_id=item_id)
    await callback.message.edit_text(
        "Введите новое <b>описание</b>:",
        reply_markup=cancel_kb(f"adm:art:view:{item_id}"),
    )
    await callback.answer()


@router.message(AdminArtStates.edit_description)
async def admin_art_edit_desc_save(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    item_id = UUID(data["edit_art_id"])
    async with bot_session() as session:
        item = await CatalogService(session).update_home_art(item_id, description=message.text.strip())
    await state.clear()
    await message.answer("Описание обновлено.", reply_markup=art_item_menu(str(item.id)))


@router.callback_query(F.data.startswith("adm:art:edit:photo:"))
async def admin_art_edit_photo_start(callback: CallbackQuery, state: FSMContext) -> None:
    item_id = callback.data.split(":")[-1]
    await state.set_state(AdminArtStates.edit_photo)
    await state.update_data(edit_art_id=item_id)
    await callback.message.edit_text(
        "Отправьте новое <b>фото</b>:",
        reply_markup=cancel_kb(f"adm:art:view:{item_id}"),
    )
    await callback.answer()


@router.message(AdminArtStates.edit_photo, F.photo)
async def admin_art_edit_photo_save(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    item_id = UUID(data["edit_art_id"])
    try:
        image_url = await upload_telegram_photo(bot, message.photo[-1].file_id)
    except Exception as exc:
        await message.answer(f"Ошибка загрузки: {exc}")
        return
    async with bot_session() as session:
        item = await CatalogService(session).update_home_art(item_id, image_url=image_url)
    await state.clear()
    await message.answer("Фото обновлено.", reply_markup=art_item_menu(str(item.id)))


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
    await _create_promo(message, state, code=None)


@router.message(AdminPromoStates.code)
async def admin_promo_code(message: Message, state: FSMContext) -> None:
    await _create_promo(message, state, code=message.text.strip())


async def _create_promo(message: Message, state: FSMContext, code: str | None) -> None:
    data = await state.get_data()
    try:
        async with bot_session() as session:
            promo = await CatalogService(session).create_promo(
                name=data["promo_name"],
                discount_percent=data["discount_percent"],
                code=code,
            )
    except ValueError as exc:
        await message.answer(str(exc))
        return
    await state.clear()
    await message.answer(
        f"Промокод создан:\n<b>{promo.code}</b> — {promo.name}, скидка {promo.discount_percent}%",
        reply_markup=promo_item_menu(str(promo.id)),
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
    await callback.message.edit_text(
        f"<b>{promo.name}</b>\nКод: <code>{promo.code}</code>\nСкидка: {promo.discount_percent}%\n"
        f"Использований: {promo.used_count}",
        reply_markup=promo_item_menu(str(promo.id)),
    )
    await callback.answer()


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
        await _save_product(message, state)


@router.message(AdminProductStates.credits_amount)
async def admin_product_credits(message: Message, state: FSMContext) -> None:
    try:
        credits = int(message.text.strip())
    except ValueError:
        await message.answer("Введите целое число.")
        return
    await state.update_data(credits_amount=credits)
    await _save_product(message, state)


async def _save_product(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    async with bot_session() as session:
        product = await CatalogService(session).create_product(
            name=data["product_name"],
            product_type=ShopProductType(data["product_type"]),
            price=data["price"],
            sale_price=data.get("sale_price"),
            gems_amount=data.get("gems_amount", 0),
            credits_amount=data.get("credits_amount", 0),
        )
    await state.clear()
    price_show = product.sale_price or product.price
    await message.answer(
        f"Товар создан: <b>{product.name}</b>\nТип: {product.product_type}\nЦена: {price_show}",
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
    await callback.message.edit_text(
        f"<b>{product.name}</b>\nТип: {product.product_type}\nЦена: {product.price}{sale}\n"
        f"Гемы: {product.gems_amount} | Кредиты: {product.credits_amount}",
        reply_markup=product_item_menu(str(product.id)),
    )
    await callback.answer()


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
