from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.schemas.catalog import PromoCodeResponse, ShopProductResponse

ADMIN_MENU_TEXT_STATS = "Статистика"
ADMIN_MENU_TEXT_USERS = "Пользователи"
ADMIN_MENU_TEXT_TOPUP_HISTORY = "История пополнений"
ADMIN_MENU_TEXT_EXPENSE_HISTORY = "История расходов"
ADMIN_MENU_TEXT_BACK_STATS = "← К статистике"
ADMIN_MENU_TEXT_BACK_USERS = "← К списку"
ADMIN_MENU_TEXT_BACK_USER = "← К пользователю"
ADMIN_MENU_TEXT_BACK_ADMIN = "« В админ-меню"
ADMIN_USERS_PAGE_PREV = "◀ Страница"
ADMIN_USERS_PAGE_NEXT = "Страница ▶"
ADMIN_USERS_SEARCH = "🔍 Поиск пользователей"
ADMIN_USERS_CLEAR_SEARCH = "✕ Сбросить поиск"
ADMIN_TOPUPS_PAGE_PREV = "◀ Назад"
ADMIN_TOPUPS_PAGE_NEXT = "Вперёд ▶"
ADMIN_TOPUPS_SEARCH = "🔍 Поиск пополнений"
ADMIN_TOPUPS_CLEAR_SEARCH = "✕ Сбросить поиск пополнений"
ADMIN_EXPENSES_SEARCH = "🔍 Поиск расходов"
ADMIN_EXPENSES_CLEAR_SEARCH = "✕ Сбросить поиск расходов"
ADMIN_USER_BLOCK = "🔒 Заблокировать"
ADMIN_USER_UNBLOCK = "✅ Разблокировать"
ADMIN_USER_EDIT_MENU = "✏️ Редактировать"
ADMIN_USER_EDIT_NAME = "✏️ Имя"
ADMIN_USER_EDIT_GEMS = "💎 Гемы"
ADMIN_USER_EDIT_CREDITS = "🎫 Кредиты"
ADMIN_USER_TOGGLE_ROLE = "👤 Сменить роль"
ADMIN_MENU_TEXT_BROADCAST = "Рассылка"
ADMIN_MENU_TEXT_CHARACTERS = "Создать персонажа"
ADMIN_MENU_TEXT_CHAR_NEW = "+ Новый персонаж"
ADMIN_MENU_TEXT_CHAR_ORDER = "Порядок на главной"
ADMIN_MENU_TEXT_CHAR_DELETE = "Удалить персонажа"
ADMIN_MENU_TEXT_PROMOS = "Промокоды"
ADMIN_CHAR_SUBMENU_TEXTS = frozenset(
    {
        ADMIN_MENU_TEXT_CHAR_NEW,
        ADMIN_MENU_TEXT_CHAR_ORDER,
        ADMIN_MENU_TEXT_CHAR_DELETE,
    }
)
ADMIN_MENU_TEXT_PRODUCTS = "Товары магазина"
ADMIN_MENU_TEXTS = frozenset(
    {
        ADMIN_MENU_TEXT_STATS,
        ADMIN_MENU_TEXT_USERS,
        ADMIN_MENU_TEXT_TOPUP_HISTORY,
        ADMIN_MENU_TEXT_EXPENSE_HISTORY,
        ADMIN_MENU_TEXT_BROADCAST,
        ADMIN_MENU_TEXT_CHARACTERS,
        ADMIN_MENU_TEXT_PROMOS,
        ADMIN_MENU_TEXT_PRODUCTS,
    }
)


def main_reply_keyboard(webapp_url: str, *, include_admin: bool = False) -> ReplyKeyboardMarkup | ReplyKeyboardRemove:
    """Persistent bottom keyboard (not tied to a single message)."""
    rows: list[list[KeyboardButton]] = []
    if include_admin:
        rows.extend(
            [
                [
                    KeyboardButton(text=ADMIN_MENU_TEXT_STATS),
                    KeyboardButton(text=ADMIN_MENU_TEXT_USERS),
                ],
                [
                    KeyboardButton(text=ADMIN_MENU_TEXT_BROADCAST),
                    KeyboardButton(text=ADMIN_MENU_TEXT_CHARACTERS),
                ],
                [
                    KeyboardButton(text=ADMIN_MENU_TEXT_PROMOS),
                    KeyboardButton(text=ADMIN_MENU_TEXT_PRODUCTS),
                ],
            ]
        )
    if not rows:
        return ReplyKeyboardRemove(remove_keyboard=True)
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        is_persistent=True,
    )


USER_FINANCE_CB = "user:finance"


def user_start_inline(webapp_url: str) -> InlineKeyboardMarkup:
    """Inline buttons under /start for all users."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть Veluna",
                    web_app=WebAppInfo(url=webapp_url),
                )
            ],
            [
                InlineKeyboardButton(text="💎 Баланс и траты", callback_data=USER_FINANCE_CB),
            ],
        ]
    )


def user_finance_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data=USER_FINANCE_CB)],
        ]
    )


def start_keyboard(webapp_url: str, *, include_admin: bool = False) -> ReplyKeyboardMarkup:
    """Alias for main menu reply keyboard."""
    return main_reply_keyboard(webapp_url, include_admin=include_admin)


def admin_main_menu(webapp_url: str) -> ReplyKeyboardMarkup:
    return main_reply_keyboard(webapp_url, include_admin=True)


def back_to_admin() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="« В админ-меню", callback_data="adm:menu")]]
    )


def stats_inline_keyboard(webapp_url: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(text="История пополнений", callback_data="adm:topups:1"),
            InlineKeyboardButton(text="История расходов", callback_data="adm:expenses:1"),
        ]
    ]
    rows.append([InlineKeyboardButton(text="« В админ-меню", callback_data="adm:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def stats_submenu_keyboard(webapp_url: str) -> ReplyKeyboardMarkup:
    """Bottom keys after admin pressed «Статистика»."""
    rows: list[list[KeyboardButton]] = [
        [
            KeyboardButton(text=ADMIN_MENU_TEXT_TOPUP_HISTORY),
            KeyboardButton(text=ADMIN_MENU_TEXT_EXPENSE_HISTORY),
        ],
        [KeyboardButton(text=ADMIN_MENU_TEXT_USERS)],
    ]
    rows.append([KeyboardButton(text=ADMIN_MENU_TEXT_BACK_ADMIN)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, is_persistent=True)


def topup_history_inline_keyboard(
    *,
    page: int,
    pages: int,
    search_active: bool = False,
    mode: str = "topups",
) -> InlineKeyboardMarkup:
    base = "adm:expenses" if mode == "expenses" else "adm:topups"
    search_text = "✕ Сбросить поиск" if search_active else "🔍 Поиск"
    rows: list[list[InlineKeyboardButton]] = []
    prev_page = max(1, page - 1)
    next_page = min(pages, page + 1)
    rows.append(
        [
            InlineKeyboardButton(text="◀ Назад", callback_data=f"{base}:{prev_page}"),
            InlineKeyboardButton(text=f"{page}/{pages}", callback_data="adm:noop"),
            InlineKeyboardButton(text="Вперёд ▶", callback_data=f"{base}:{next_page}"),
        ]
    )
    if search_active:
        rows.append([InlineKeyboardButton(text=search_text, callback_data=f"{base}:clear")])
    else:
        rows.append([InlineKeyboardButton(text=search_text, callback_data=f"{base}:search")])
    rows.append(
        [
            InlineKeyboardButton(text="← К статистике", callback_data="adm:stats"),
        ]
    )
    rows.append([InlineKeyboardButton(text="« В админ-меню", callback_data="adm:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def topup_history_keyboard(
    *,
    page: int,
    pages: int,
    search_active: bool = False,
    mode: str = "topups",
) -> ReplyKeyboardMarkup:
    search_button = ADMIN_EXPENSES_SEARCH if mode == "expenses" else ADMIN_TOPUPS_SEARCH
    clear_button = ADMIN_EXPENSES_CLEAR_SEARCH if mode == "expenses" else ADMIN_TOPUPS_CLEAR_SEARCH
    other_history = ADMIN_MENU_TEXT_TOPUP_HISTORY if mode == "expenses" else ADMIN_MENU_TEXT_EXPENSE_HISTORY
    rows: list[list[KeyboardButton]] = []
    rows.append(
        [
            KeyboardButton(text=ADMIN_TOPUPS_PAGE_PREV),
            KeyboardButton(text=ADMIN_TOPUPS_PAGE_NEXT),
        ]
    )
    if search_active:
        rows.append([KeyboardButton(text=clear_button)])
    else:
        rows.append([KeyboardButton(text=search_button)])
    rows.append(
        [
            KeyboardButton(text=other_history),
            KeyboardButton(text=ADMIN_MENU_TEXT_USERS),
        ]
    )
    rows.append(
        [
            KeyboardButton(text=ADMIN_MENU_TEXT_BACK_STATS),
        ]
    )
    rows.append([KeyboardButton(text=ADMIN_MENU_TEXT_BACK_ADMIN)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, is_persistent=True)


def users_list_keyboard(
    labels: list[str],
    *,
    page: int,
    pages: int,
    search_active: bool = False,
) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=label)] for label in labels]
    nav: list[KeyboardButton] = []
    if page > 1:
        nav.append(KeyboardButton(text=ADMIN_USERS_PAGE_PREV))
    if page < pages:
        nav.append(KeyboardButton(text=ADMIN_USERS_PAGE_NEXT))
    if nav:
        rows.append(nav)
    if search_active:
        rows.append([KeyboardButton(text=ADMIN_USERS_CLEAR_SEARCH)])
    else:
        rows.append([KeyboardButton(text=ADMIN_USERS_SEARCH)])
    rows.append([KeyboardButton(text=ADMIN_MENU_TEXT_BACK_ADMIN)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, is_persistent=True)


def user_detail_keyboard(*, is_banned: bool) -> ReplyKeyboardMarkup:
    ban = ADMIN_USER_UNBLOCK if is_banned else ADMIN_USER_BLOCK
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ban)],
            [KeyboardButton(text=ADMIN_USER_EDIT_MENU)],
            [KeyboardButton(text=ADMIN_MENU_TEXT_BACK_USERS)],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def user_edit_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=ADMIN_USER_EDIT_NAME),
                KeyboardButton(text=ADMIN_USER_EDIT_GEMS),
            ],
            [
                KeyboardButton(text=ADMIN_USER_EDIT_CREDITS),
                KeyboardButton(text=ADMIN_USER_TOGGLE_ROLE),
            ],
            [KeyboardButton(text=ADMIN_MENU_TEXT_BACK_USER)],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def _character_list_label(ch, position: int | None) -> str:
    prefix = f"{position}. " if position else ""
    name = (ch.name or "").strip()
    subtitle = (ch.subtitle or "").strip()
    if subtitle and subtitle.lower() != name.lower():
        return f"{prefix}{name[:14]} · {subtitle[:10]}"
    return f"{prefix}{name[:28]}"


def characters_menu(characters: list, catalog_positions: dict | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    positions = catalog_positions or {}
    for ch in characters[:15]:
        if not ch.is_active or ch.is_hidden:
            continue
        label = _character_list_label(ch, positions.get(ch.id))
        builder.row(
            InlineKeyboardButton(
                text=label[:64],
                callback_data=f"adm:char:view:{ch.id}",
            )
        )
    return builder.as_markup()


def characters_submenu_keyboard() -> ReplyKeyboardMarkup:
    """Bottom keys after admin pressed «Создать персонажа»."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ADMIN_MENU_TEXT_CHAR_NEW)],
            [KeyboardButton(text=ADMIN_MENU_TEXT_CHAR_ORDER)],
            [KeyboardButton(text=ADMIN_MENU_TEXT_CHAR_DELETE)],
            [KeyboardButton(text=ADMIN_MENU_TEXT_BACK_ADMIN)],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def character_delete_list_menu(characters: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    active = [ch for ch in characters if ch.is_active and not ch.is_hidden]
    if not active:
        builder.row(InlineKeyboardButton(text="« Назад", callback_data="adm:chars"))
        return builder.as_markup()
    for ch in active[:15]:
        label = f"🗑 {ch.name[:28]}"
        builder.row(
            InlineKeyboardButton(
                text=label[:64],
                callback_data=f"adm:char:del:ask:{ch.id}",
            )
        )
    builder.row(InlineKeyboardButton(text="« Назад", callback_data="adm:chars"))
    return builder.as_markup()


def character_delete_confirm_menu(character_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data=f"adm:char:del:yes:{character_id}",
        )
    )
    builder.row(InlineKeyboardButton(text="« Отмена", callback_data="adm:chars"))
    return builder.as_markup()


def character_item_menu(character_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Сценарии",
            callback_data=f"adm:char:scenarios:{character_id}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Рассказчики",
            callback_data=f"adm:char:narrators:{character_id}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="+ Добавить сценарий",
            callback_data=f"adm:scen:add:{character_id}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📋 Позиция на главной",
            callback_data=f"adm:char:order:view:{character_id}",
        )
    )
    builder.row(InlineKeyboardButton(text="« К списку", callback_data="adm:chars"))
    return builder.as_markup()


def character_order_list_menu(catalog: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, ch in enumerate(catalog[:15], start=1):
        label = f"{i}. {ch.name[:22]}"
        if ch.subtitle:
            label = f"{i}. {ch.name[:12]} · {ch.subtitle[:10]}"
        builder.row(
            InlineKeyboardButton(
                text=label[:64],
                callback_data=f"adm:char:order:view:{ch.id}",
            )
        )
    builder.row(InlineKeyboardButton(text="« К персонажам", callback_data="adm:chars"))
    return builder.as_markup()


def character_order_controls_menu(character_id: str, position: int, total: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    row: list[InlineKeyboardButton] = []
    if position > 1:
        row.append(
            InlineKeyboardButton(
                text="⬆️ Вверх",
                callback_data=f"adm:char:order:up:{character_id}",
            )
        )
    if position < total:
        row.append(
            InlineKeyboardButton(
                text="⬇️ Вниз",
                callback_data=f"adm:char:order:down:{character_id}",
            )
        )
    if row:
        builder.row(*row)
    if position > 1:
        builder.row(
            InlineKeyboardButton(
                text="🥇 На первое место",
                callback_data=f"adm:char:order:top:{character_id}",
            )
        )
    builder.row(InlineKeyboardButton(text="« К порядку", callback_data="adm:char:order"))
    builder.row(InlineKeyboardButton(text="« К персонажам", callback_data="adm:chars"))
    return builder.as_markup()


def scenarios_menu(character_id: str, scenarios: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for sc in scenarios[:15]:
        builder.row(
            InlineKeyboardButton(
                text=sc.title[:48],
                callback_data=f"adm:scen:view:{sc.id}",
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="+ Новый сценарий",
            callback_data=f"adm:scen:add:{character_id}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="« К персонажу",
            callback_data=f"adm:char:view:{character_id}",
        )
    )
    return builder.as_markup()


def char_create_scenario_kb(character_id: str, *, can_finish: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="➕ Ещё сценарий",
            callback_data=f"adm:char:create:scen:more:{character_id}",
        )
    )
    if can_finish:
        builder.row(
            InlineKeyboardButton(
                text="➡️ К рассказчикам",
                callback_data=f"adm:char:create:narr:start:{character_id}",
            )
        )
    builder.row(InlineKeyboardButton(text="« К персонажу", callback_data=f"adm:char:view:{character_id}"))
    return builder.as_markup()


def char_create_narrator_kb(character_id: str, *, can_finish: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="➕ Ещё рассказчик",
            callback_data=f"adm:char:create:narr:more:{character_id}",
        )
    )
    if can_finish:
        builder.row(
            InlineKeyboardButton(
                text="✅ Завершить создание",
                callback_data=f"adm:char:create:done:{character_id}",
            )
        )
    builder.row(InlineKeyboardButton(text="« К персонажу", callback_data=f"adm:char:view:{character_id}"))
    return builder.as_markup()


def scenario_item_menu(scenario_id: str, character_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🖼 Фото",
            callback_data=f"adm:scen:photo:{scenario_id}",
        ),
        InlineKeyboardButton(
            text="Удалить сценарий",
            callback_data=f"adm:scen:del:{scenario_id}",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="« К сценариям",
            callback_data=f"adm:char:scenarios:{character_id}",
        )
    )
    return builder.as_markup()


def narrators_menu(character_id: str, narrators: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for narrator in narrators[:15]:
        label = narrator.name[:40]
        if narrator.price:
            label = f"{label} · {narrator.price}❤️"
        builder.row(
            InlineKeyboardButton(
                text=label[:48],
                callback_data=f"adm:narr:view:{narrator.id}",
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="+ Новый рассказчик",
            callback_data=f"adm:narr:add:{character_id}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="« К персонажу",
            callback_data=f"adm:char:view:{character_id}",
        )
    )
    return builder.as_markup()


def narrator_item_menu(narrator_id: str, character_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✏️ Цена (сердца)",
            callback_data=f"adm:narr:price:{narrator_id}",
        ),
        InlineKeyboardButton(
            text="🖼 Фото",
            callback_data=f"adm:narr:photo:{narrator_id}",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="Удалить рассказчика",
            callback_data=f"adm:narr:del:{narrator_id}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="« К рассказчикам",
            callback_data=f"adm:char:narrators:{character_id}",
        )
    )
    return builder.as_markup()


def promos_menu(promos: list[PromoCodeResponse]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for promo in promos[:15]:
        builder.row(
            InlineKeyboardButton(
                text=f"{promo.code} — {promo.discount_percent}%",
                callback_data=f"adm:promo:view:{promo.id}",
            )
        )
    builder.row(InlineKeyboardButton(text="+ Создать промокод", callback_data="adm:promo:add"))
    builder.row(InlineKeyboardButton(text="« Назад", callback_data="adm:menu"))
    return builder.as_markup()


def promo_item_menu(promo_id: str, *, is_active: bool = True) -> InlineKeyboardMarkup:
    toggle = "Выключить" if is_active else "Включить"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=toggle, callback_data=f"adm:promo:toggle:{promo_id}")],
            [InlineKeyboardButton(text="Лимит использований", callback_data=f"adm:promo:max:{promo_id}")],
            [InlineKeyboardButton(text="Удалить", callback_data=f"adm:promo:del:{promo_id}")],
            [InlineKeyboardButton(text="« К списку", callback_data="adm:promos")],
        ]
    )


def products_menu(products: list[ShopProductResponse]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for product in products[:15]:
        price = product.sale_price or product.price
        builder.row(
            InlineKeyboardButton(
                text=f"{product.name} ({product.product_type}) — {price}",
                callback_data=f"adm:prod:view:{product.id}",
            )
        )
    builder.row(InlineKeyboardButton(text="+ Добавить товар", callback_data="adm:prod:add"))
    builder.row(InlineKeyboardButton(text="« Назад", callback_data="adm:menu"))
    return builder.as_markup()


def product_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Гемы", callback_data="adm:prod:type:gems"),
                InlineKeyboardButton(text="Кредиты", callback_data="adm:prod:type:credits"),
            ],
            [InlineKeyboardButton(text="Набор", callback_data="adm:prod:type:bundle")],
            [InlineKeyboardButton(text="Отмена", callback_data="adm:products")],
        ]
    )


def product_item_menu(product_id: str, *, is_active: bool = True) -> InlineKeyboardMarkup:
    toggle = "Скрыть из магазина" if is_active else "Показать в магазине"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Изменить фото", callback_data=f"adm:prod:edit:photo:{product_id}")],
            [InlineKeyboardButton(text=toggle, callback_data=f"adm:prod:toggle:{product_id}")],
            [InlineKeyboardButton(text="Удалить", callback_data=f"adm:prod:del:{product_id}")],
            [InlineKeyboardButton(text="« К списку", callback_data="adm:products")],
        ]
    )


def broadcast_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить всем", callback_data="adm:broadcast:confirm"),
                InlineKeyboardButton(text="Отмена", callback_data="adm:broadcast:cancel"),
            ],
        ]
    )


def cancel_kb(back: str = "adm:menu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Отмена", callback_data=back)]]
    )
