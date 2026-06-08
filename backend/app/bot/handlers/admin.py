import logging
from uuid import UUID

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardMarkup
from sqlalchemy import and_, or_, select

from app.bot.db import bot_session
from app.bot.filters import AdminFilter, is_bot_admin
from app.bot.keyboards import (
    ADMIN_MENU_TEXT_BROADCAST,
    ADMIN_MENU_TEXT_PRODUCTS,
    ADMIN_MENU_TEXT_PROMOS,
    ADMIN_MENU_TEXT_STATS,
    ADMIN_MENU_TEXT_EXPENSE_HISTORY,
    ADMIN_MENU_TEXT_TOPUP_HISTORY,
    admin_main_menu,
    broadcast_confirm_kb,
    cancel_kb,
    main_reply_keyboard,
    product_item_menu,
    product_type_keyboard,
    products_menu,
    promo_item_menu,
    promos_menu,
    stats_inline_keyboard,
    topup_history_keyboard,
    topup_history_inline_keyboard,
    ADMIN_EXPENSES_CLEAR_SEARCH,
    ADMIN_EXPENSES_SEARCH,
    ADMIN_TOPUPS_CLEAR_SEARCH,
    ADMIN_TOPUPS_PAGE_NEXT,
    ADMIN_TOPUPS_PAGE_PREV,
    ADMIN_TOPUPS_SEARCH,
)
from app.bot.states import AdminBroadcastStates, AdminProductStates, AdminPromoStates, AdminTopupStates
from app.services.broadcast_service import BroadcastService
from app.bot.utils import upload_telegram_photo
from app.core.config import get_settings
from app.models import Purchase, PurchaseStatus, ShopProductType, Transaction, TransactionType, User
from app.services.catalog_service import CatalogService

logger = logging.getLogger(__name__)

router = Router(name="admin")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())

TOPUP_HISTORY_PAGE_SIZE = 10
FINANCE_MODE_TOPUPS = "topups"
FINANCE_MODE_EXPENSES = "expenses"


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
    from app.bot.finance_display import format_platform_finance_for_stats
    from app.repositories.generation_repository import PaymentRepository

    async with bot_session() as session:
        repo = PaymentRepository(session)
        s = await CatalogService(session).user_stats()
        finance = await repo.get_platform_finance_stats()
        api_costs = await repo.get_platform_api_cost_stats()

    finance_block = format_platform_finance_for_stats(finance, api_costs)

    return (
        "<b>Статистика Veluna</b>\n\n"
        "<b>Пользователи</b>\n"
        f"• Зарегистрировано: <b>{s.total_users}</b>\n"
        f"• Пользовались сервисом (уник.): <b>{s.unique_users_ever}</b>\n"
        f"• Активны сейчас (24 ч): <b>{s.active_users_24h}</b>\n"
        f"• Активны (7 дней): <b>{s.active_users_7d}</b>\n"
        f"• Заблокировано: <b>{s.banned_users}</b>\n\n"
        f"{finance_block}\n\n"
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
    inline_kb = stats_inline_keyboard(settings.telegram_webapp_url)
    try:
        text = await _stats_text()
        text += "\n\n<i>Кнопки управления — под этим сообщением.</i>"
    except Exception as exc:
        logger.exception("Admin stats failed: %s", exc)
        text = (
            "<b>Статистика</b>\n\n"
            "Не удалось загрузить данные. Локально:\n"
            "<code>docker compose up postgres redis -d</code>\n"
            "<code>cd backend; .\\.venv\\Scripts\\alembic upgrade head</code>"
        )
    await message.answer(text, reply_markup=inline_kb)
    logger.info("Admin stats keyboard sent (Пользователи submenu)")


def _user_label(user: User) -> str:
    if user.username:
        return f"@{user.username}"
    name = " ".join(part for part in (user.first_name, user.last_name) if part)
    return name or f"tg:{user.telegram_id}"


def _event_sort_key(event: dict) -> object:
    return event["created_at"]


def _format_finance_event(index: int, event: dict) -> str:
    user = event["user"]
    created_at = event["created_at"]
    created = created_at.strftime("%d.%m %H:%M") if created_at else "—"
    kind = event["kind"]

    if kind == "purchase":
        purchase: Purchase = event["record"]
        payment = f"\n   ID: <code>{purchase.telegram_payment_id}</code>" if purchase.telegram_payment_id else ""
        gems = f" · +<b>{purchase.gems_amount}</b> гемов" if purchase.gems_amount else ""
        return (
            f"{index}. 🟢 <b>Пополнение</b> · <b>{_user_label(user)}</b>\n"
            f"   <b>{purchase.stars_amount}</b> Stars{gems} · {created}"
            f"{payment}"
        )

    tx: Transaction = event["record"]
    amount_abs = abs(tx.amount)
    from app.repositories.generation_repository import _transaction_currency

    currency = _transaction_currency(tx)
    cur_icon = "💎" if currency == "gems" else "❤️"

    if tx.type == TransactionType.SPEND:
        if tx.description == "Image generation":
            label = "Генерация изображения"
        elif tx.description.startswith("Message to "):
            label = tx.description.replace("Message to ", "Чат с ", 1)
        elif tx.description.startswith("Сообщение в чате"):
            label = tx.description
        else:
            label = tx.description or "Расход"
        ref = f"\n   ref: <code>{tx.reference_id}</code>" if tx.reference_id else ""
        tx_meta = tx.metadata_ or {}
        api_line = ""
        if tx_meta.get("api_cost_rub") is not None:
            from app.services.api_cost_service import format_rub

            api_line = f"\n   API: <b>{format_rub(float(tx_meta['api_cost_rub']))}</b> ₽"
        elif tx_meta.get("api_buzz_cost") is not None:
            api_line = f"\n   API: <b>{tx_meta['api_buzz_cost']}</b> Buzz"
        return (
            f"{index}. 🔴 <b>Расход</b> · <b>{_user_label(user)}</b>\n"
            f"   −<b>{amount_abs}</b>{cur_icon} · {label} · баланс {tx.balance_after} · {created}"
            f"{api_line}{ref}"
        )

    if tx.type == TransactionType.BONUS:
        label = "Бонус"
    elif tx.type == TransactionType.ADMIN_ADJUST:
        label = "Админское начисление"
    elif tx.type == TransactionType.REFUND:
        label = "Возврат"
    elif tx.type == TransactionType.PURCHASE:
        label = tx.description or "Покупка"
    else:
        label = tx.description or tx.type.value
    return (
        f"{index}. 🟡 <b>{label}</b> · <b>{_user_label(user)}</b>\n"
        f"   +<b>{amount_abs}</b>{cur_icon} · баланс {tx.balance_after} · {created}"
    )


def _finance_title(mode: str) -> str:
    return "История расходов" if mode == FINANCE_MODE_EXPENSES else "История пополнений"


def _finance_search_prompt(mode: str) -> str:
    if mode == FINANCE_MODE_EXPENSES:
        return (
            "<b>Поиск расходов</b>\n\n"
            "Введите username, имя, Telegram ID, описание или reference ID.\n\n"
            "<i>Отмена: /cancel</i>"
        )
    return (
        "<b>Поиск пополнений</b>\n\n"
        "Введите username, имя, Telegram ID, ID платежа, описание или reference ID.\n\n"
        "<i>Отмена: /cancel</i>"
    )


async def _load_finance_history(
    page: int,
    *,
    mode: str,
    search_query: str | None = None,
) -> tuple[list[dict], int]:
    q = (search_query or "").strip()
    async with bot_session() as session:
        tx_base = (
            select(Transaction, User)
            .join(User, User.id == Transaction.user_id)
        )
        if mode == FINANCE_MODE_EXPENSES:
            tx_base = tx_base.where(Transaction.type == TransactionType.SPEND)
            purchase_base = None
        else:
            tx_base = tx_base.where(
                or_(
                    Transaction.type.in_(
                        [
                            TransactionType.BONUS,
                            TransactionType.ADMIN_ADJUST,
                            TransactionType.REFUND,
                        ]
                    ),
                    and_(
                        Transaction.amount > 0,
                        Transaction.metadata_["currency"].as_string() == "credits",
                    ),
                )
            )
            purchase_base = (
                select(Purchase, User)
                .join(User, User.id == Purchase.user_id)
                .where(Purchase.status == PurchaseStatus.COMPLETED)
            )
        if q:
            like = f"%{q.lstrip('@')}%"
            common_filters = [
                User.username.ilike(like),
                User.first_name.ilike(like),
                User.last_name.ilike(like),
            ]
            if q.isdigit():
                common_filters.append(User.telegram_id == int(q))
            tx_base = tx_base.where(or_(*(common_filters + [
                Transaction.description.ilike(f"%{q}%"),
                Transaction.reference_id.ilike(f"%{q}%"),
            ])))
            if purchase_base is not None:
                purchase_base = purchase_base.where(or_(*(common_filters + [
                    Purchase.telegram_payment_id.ilike(f"%{q}%"),
                ])))

        tx_rows = (await session.execute(tx_base)).all()
        events: list[dict] = [
            {"kind": "transaction", "record": tx, "user": user, "created_at": tx.created_at}
            for tx, user in tx_rows
        ]
        if purchase_base is not None:
            purchase_rows = (await session.execute(purchase_base)).all()
            events.extend(
                {"kind": "purchase", "record": purchase, "user": user, "created_at": purchase.created_at}
                for purchase, user in purchase_rows
            )
        events.sort(key=_event_sort_key, reverse=True)

        total = len(events)
        offset = (max(1, page) - 1) * TOPUP_HISTORY_PAGE_SIZE
        return events[offset:offset + TOPUP_HISTORY_PAGE_SIZE], total


async def _send_finance_history(
    message: Message,
    state: FSMContext,
    page: int = 1,
    *,
    mode: str,
    search_query: str | None = None,
    inline: bool = False,
    edit_existing: bool = False,
) -> None:
    rows, total = await _load_finance_history(page, mode=mode, search_query=search_query)
    pages = max(1, (total + TOPUP_HISTORY_PAGE_SIZE - 1) // TOPUP_HISTORY_PAGE_SIZE) if total else 1
    page = min(max(1, page), pages)
    if page > 1 and not rows:
        rows, total = await _load_finance_history(page, mode=mode, search_query=search_query)

    await state.update_data(
        topups_page=page,
        topups_pages=pages,
        topups_search_query=(search_query or "").strip(),
        finance_mode=mode,
    )

    title_text = _finance_title(mode)
    if search_query:
        title = (
            f"<b>{title_text}</b>\n"
            f"Поиск: <code>{search_query}</code>\n"
            f"Найдено: <b>{total}</b> · стр. {page}/{pages}"
        )
    else:
        title = f"<b>{title_text}</b> · стр. {page}/{pages} · всего {total}"

    if rows:
        start = (page - 1) * TOPUP_HISTORY_PAGE_SIZE + 1
        body = "\n\n".join(
            _format_finance_event(start + i, event)
            for i, event in enumerate(rows)
        )
    else:
        if search_query:
            body = "<i>Записей не найдено.</i>"
        elif mode == FINANCE_MODE_EXPENSES:
            body = "<i>Расходов пока нет.</i>"
        else:
            body = "<i>Пополнений пока нет.</i>"

    markup = (
        topup_history_inline_keyboard(
            page=page,
            pages=pages,
            search_active=bool(search_query),
            mode=mode,
        )
        if inline
        else topup_history_keyboard(
            page=page,
            pages=pages,
            search_active=bool(search_query),
            mode=mode,
        )
    )
    text = f"{title}\n\n{body}"
    if edit_existing:
        data = await state.get_data()
        message_id = data.get("finance_message_id")
        chat_id = data.get("finance_chat_id") or message.chat.id
        if message_id:
            try:
                await message.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=int(message_id),
                    text=text,
                    reply_markup=markup if inline else None,
                )
                return
            except Exception as exc:
                if isinstance(exc, TelegramBadRequest) and "message is not modified" in str(exc):
                    return
                logger.exception("Failed to edit finance history message")

    sent = await message.answer(
        text,
        reply_markup=markup,
    )
    await state.update_data(finance_chat_id=sent.chat.id, finance_message_id=sent.message_id)


@router.message(F.text == ADMIN_MENU_TEXT_STATS)
async def admin_stats_message(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _send_stats(message, message.from_user)


@router.callback_query(F.data == "adm:stats")
async def admin_stats(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await _send_stats(callback.message, callback.from_user)
    await callback.answer()


@router.callback_query(F.data == "adm:noop")
async def admin_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data.regexp(r"^adm:(topups|expenses):\d+$"))
async def admin_finance_history_page_cb(callback: CallbackQuery, state: FSMContext) -> None:
    mode = FINANCE_MODE_EXPENSES if callback.data.startswith("adm:expenses:") else FINANCE_MODE_TOPUPS
    page = int(callback.data.rsplit(":", 1)[-1])
    data = await state.get_data()
    q = (data.get("topups_search_query") or "").strip() or None
    if data.get("finance_mode") != mode:
        q = None
    await state.set_state(None)
    await _send_finance_history(
        callback.message,
        state,
        page=page,
        mode=mode,
        search_query=q,
        inline=True,
        edit_existing=True,
    )
    await callback.answer()


@router.callback_query(F.data.in_({"adm:topups:search", "adm:expenses:search"}))
async def admin_finance_history_search_cb(callback: CallbackQuery, state: FSMContext) -> None:
    mode = FINANCE_MODE_EXPENSES if callback.data.startswith("adm:expenses:") else FINANCE_MODE_TOPUPS
    await state.set_state(AdminTopupStates.search)
    await state.update_data(finance_mode=mode)
    await callback.message.answer(
        _finance_search_prompt(mode),
        reply_markup=topup_history_keyboard(page=1, pages=1, mode=mode),
    )
    await callback.answer()


@router.callback_query(F.data.in_({"adm:topups:clear", "adm:expenses:clear"}))
async def admin_finance_history_clear_cb(callback: CallbackQuery, state: FSMContext) -> None:
    mode = FINANCE_MODE_EXPENSES if callback.data.startswith("adm:expenses:") else FINANCE_MODE_TOPUPS
    await state.set_state(None)
    await _send_finance_history(callback.message, state, page=1, mode=mode, edit_existing=True)
    await callback.answer("Поиск сброшен")


@router.message(F.text == ADMIN_MENU_TEXT_TOPUP_HISTORY)
async def admin_topup_history_open(message: Message, state: FSMContext) -> None:
    await state.set_state(None)
    await _send_finance_history(message, state, page=1, mode=FINANCE_MODE_TOPUPS)


@router.message(F.text == ADMIN_MENU_TEXT_EXPENSE_HISTORY)
async def admin_expense_history_open(message: Message, state: FSMContext) -> None:
    await state.set_state(None)
    await _send_finance_history(message, state, page=1, mode=FINANCE_MODE_EXPENSES)


@router.message(F.text.in_({ADMIN_TOPUPS_PAGE_PREV, ADMIN_TOPUPS_PAGE_NEXT}))
async def admin_topup_history_page(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    page = int(data.get("topups_page", 1))
    pages = int(data.get("topups_pages", 1))
    mode = data.get("finance_mode") or FINANCE_MODE_TOPUPS
    if message.text == ADMIN_TOPUPS_PAGE_PREV:
        page = max(1, page - 1)
    else:
        page = min(pages, page + 1)
    q = (data.get("topups_search_query") or "").strip() or None
    await _send_finance_history(
        message,
        state,
        page=page,
        mode=mode,
        search_query=q,
        edit_existing=True,
    )


@router.message(F.text.in_({ADMIN_TOPUPS_SEARCH, ADMIN_EXPENSES_SEARCH}))
async def admin_finance_history_search_start(message: Message, state: FSMContext) -> None:
    mode = FINANCE_MODE_EXPENSES if message.text == ADMIN_EXPENSES_SEARCH else FINANCE_MODE_TOPUPS
    await state.set_state(AdminTopupStates.search)
    await state.update_data(finance_mode=mode)
    await message.answer(
        _finance_search_prompt(mode),
        reply_markup=topup_history_keyboard(page=1, pages=1, mode=mode),
    )


@router.message(F.text.in_({ADMIN_TOPUPS_CLEAR_SEARCH, ADMIN_EXPENSES_CLEAR_SEARCH}))
async def admin_finance_history_search_clear(message: Message, state: FSMContext) -> None:
    mode = FINANCE_MODE_EXPENSES if message.text == ADMIN_EXPENSES_CLEAR_SEARCH else FINANCE_MODE_TOPUPS
    await state.set_state(None)
    await _send_finance_history(message, state, page=1, mode=mode, edit_existing=True)


@router.message(AdminTopupStates.search)
async def admin_topup_history_search_run(message: Message, state: FSMContext) -> None:
    query = (message.text or "").strip()
    if not query:
        await message.answer("Введите непустой запрос для поиска.")
        return
    data = await state.get_data()
    mode = data.get("finance_mode") or FINANCE_MODE_TOPUPS
    await state.set_state(None)
    await _send_finance_history(
        message,
        state,
        page=1,
        mode=mode,
        search_query=query,
        edit_existing=True,
    )


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
