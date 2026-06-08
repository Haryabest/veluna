"""Format user finance stats for Telegram bot messages."""


def format_user_finance_stats(stats: dict) -> str:
    balance = stats.get("balance") or {}
    spent = stats.get("spent") or {}
    deposited = stats.get("deposited") or {}
    purchases = stats.get("purchases") or {}
    lifetime = stats.get("lifetime") or {}

    gems = int(balance.get("gems") or 0)
    credits = int(balance.get("credits") or 0)
    gems_spent = int(spent.get("gems") or 0)
    credits_spent = int(spent.get("credits") or 0)
    gems_dep = int(deposited.get("gems") or 0)
    credits_dep = int(deposited.get("credits") or 0)

    lines = [
        "<b>💎 Баланс</b>",
        f"Гемы: <b>{gems}</b> 💎",
        f"Сердца: <b>{credits}</b> ❤️",
        "",
        "<b>📉 Потрачено</b>",
        f"Гемы: <b>−{gems_spent}</b> 💎",
        f"Сердца: <b>−{credits_spent}</b> ❤️",
        "",
        "<b>📈 Пополнено</b>",
        f"Гемы: <b>+{gems_dep}</b> 💎",
        f"Сердца: <b>+{credits_dep}</b> ❤️",
    ]

    purchase_count = int(purchases.get("completed_count") or 0)
    if purchase_count > 0:
        stars = int(purchases.get("stars_total") or 0)
        lines.extend(
            [
                "",
                "<b>🛒 Покупки</b>",
                f"Оплат: <b>{purchase_count}</b>",
            ]
        )
        if stars > 0:
            lines.append(f"Stars: <b>{stars}</b> ⭐")

    total_earned = int(lifetime.get("total_earned") or 0)
    total_spent = int(lifetime.get("total_spent") or 0)
    if total_earned or total_spent:
        lines.extend(
            [
                "",
                "<i>За всё время: получено {earned}, потрачено {spent}</i>".format(
                    earned=total_earned,
                    spent=total_spent,
                ),
            ]
        )

    return "\n".join(lines)


def format_platform_finance_summary(stats: dict, *, mode: str) -> str:
    """Short summary block for admin expense/deposit history screens."""
    balance = stats.get("balance") or {}
    spent = stats.get("spent") or {}
    deposited = stats.get("deposited") or {}
    purchases = stats.get("purchases") or {}

    lines = [
        "<b>📊 Итого по сервису</b>",
        f"Баланс пользователей: 💎 <b>{balance.get('gems', 0)}</b> · ❤️ <b>{balance.get('credits', 0)}</b>",
    ]

    if mode == "expenses":
        lines.append(
            f"Потрачено всего: 💎 <b>{spent.get('gems', 0)}</b> · ❤️ <b>{spent.get('credits', 0)}</b>"
        )
    else:
        lines.append(
            f"Пополнено всего: 💎 <b>{deposited.get('gems', 0)}</b> · ❤️ <b>{deposited.get('credits', 0)}</b>"
        )
        count = int(purchases.get("completed_count") or 0)
        stars = int(purchases.get("stars_total") or 0)
        if count > 0:
            lines.append(f"Покупок Stars: <b>{count}</b> · ⭐ <b>{stars}</b>")

    return "\n".join(lines)


def format_platform_finance_for_stats(stats: dict, api_costs: dict | None = None) -> str:
    """Finance block on main admin «Статистика» screen."""
    from app.services.api_cost_service import format_rub

    balance = stats.get("balance") or {}
    deposited = stats.get("deposited") or {}
    purchases = stats.get("purchases") or {}
    api = api_costs or {}
    chat = api.get("chat") or {}
    image = api.get("image") or {}

    lines = [
        "<b>Баланс (все пользователи)</b>",
        f"• Гемы: <b>{balance.get('gems', 0)}</b> 💎",
        f"• Сердца: <b>{balance.get('credits', 0)}</b> ❤️",
        "",
        "<b>Расходы API</b>",
        f"• Чат (GenAPI): <b>{format_rub(float(chat.get('rub', 0)))}</b> ₽",
        f"• Фото (Civitai): <b>{image.get('buzz', 0)}</b> Buzz",
        "",
        "<b>Пополнения</b>",
        f"• Пополнено гемов: <b>{deposited.get('gems', 0)}</b> 💎",
        f"• Пополнено сердец: <b>{deposited.get('credits', 0)}</b> ❤️",
    ]

    count = int(purchases.get("completed_count") or 0)
    stars = int(purchases.get("stars_total") or 0)
    gems_bought = int(purchases.get("gems_total") or 0)
    if count > 0:
        lines.extend(
            [
                "",
                "<b>Покупки Stars</b>",
                f"• Оплат: <b>{count}</b>",
                f"• Stars: <b>{stars}</b> ⭐",
                f"• Гемов с покупок: <b>{gems_bought}</b> 💎",
            ]
        )

    return "\n".join(lines)
