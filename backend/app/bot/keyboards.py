from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.schemas.catalog import HomeArtResponse, PromoCodeResponse, ShopProductResponse


def start_keyboard(webapp_url: str, *, include_admin: bool = False) -> InlineKeyboardMarkup:
    """Start screen: Mini App + admin sections (for admins only)."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Открыть Veluna",
            web_app=WebAppInfo(url=webapp_url),
        )
    )
    if include_admin:
        builder.row(
            InlineKeyboardButton(text="Статистика", callback_data="adm:stats"),
            InlineKeyboardButton(text="Рассылка", callback_data="adm:broadcast"),
        )
        builder.row(
            InlineKeyboardButton(text="Арт на главной", callback_data="adm:arts"),
            InlineKeyboardButton(text="Промокоды", callback_data="adm:promos"),
        )
        builder.row(InlineKeyboardButton(text="Товары магазина", callback_data="adm:products"))
    return builder.as_markup()


def admin_main_menu(webapp_url: str) -> InlineKeyboardMarkup:
    """Back to start menu (adm:menu)."""
    return start_keyboard(webapp_url, include_admin=True)


def back_to_admin() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="« В админ-меню", callback_data="adm:menu")]]
    )


def arts_menu(items: list[HomeArtResponse]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in items[:15]:
        builder.row(
            InlineKeyboardButton(
                text=item.title[:32],
                callback_data=f"adm:art:view:{item.id}",
            )
        )
    builder.row(InlineKeyboardButton(text="+ Добавить арт", callback_data="adm:art:add"))
    builder.row(InlineKeyboardButton(text="« Назад", callback_data="adm:menu"))
    return builder.as_markup()


def art_item_menu(item_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Изменить название", callback_data=f"adm:art:edit:title:{item_id}"))
    builder.row(InlineKeyboardButton(text="Изменить описание", callback_data=f"adm:art:edit:desc:{item_id}"))
    builder.row(InlineKeyboardButton(text="Изменить фото", callback_data=f"adm:art:edit:photo:{item_id}"))
    builder.row(InlineKeyboardButton(text="Удалить", callback_data=f"adm:art:del:{item_id}"))
    builder.row(InlineKeyboardButton(text="« К списку", callback_data="adm:arts"))
    return builder.as_markup()


def art_edit_cancel(item_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Отмена", callback_data=f"adm:art:view:{item_id}")]]
    )


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


def promo_item_menu(promo_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
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


def product_item_menu(product_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Удалить", callback_data=f"adm:prod:del:{product_id}")],
            [InlineKeyboardButton(text="« К списку", callback_data="adm:products")],
        ]
    )


def cancel_kb(back: str = "adm:menu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Отмена", callback_data=back)]]
    )
