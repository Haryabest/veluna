from uuid import UUID

from aiogram import F, Router
from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.db import bot_session
from app.bot.filters import AdminFilter
from app.bot.keyboards import (
    ADMIN_MENU_TEXT_BACK_ADMIN,
    main_reply_keyboard,
    ADMIN_MENU_TEXT_BACK_STATS,
    ADMIN_MENU_TEXT_BACK_USER,
    ADMIN_MENU_TEXT_BACK_USERS,
    ADMIN_MENU_TEXT_USERS,
    ADMIN_USER_BLOCK,
    ADMIN_USER_EDIT_CREDITS,
    ADMIN_USER_EDIT_GEMS,
    ADMIN_USER_EDIT_MENU,
    ADMIN_USER_EDIT_NAME,
    ADMIN_USER_TOGGLE_ROLE,
    ADMIN_USER_UNBLOCK,
    ADMIN_USERS_PAGE_NEXT,
    ADMIN_USERS_PAGE_PREV,
    ADMIN_USERS_CLEAR_SEARCH,
    ADMIN_USERS_SEARCH,
    stats_submenu_keyboard,
    user_detail_keyboard,
    user_edit_keyboard,
    users_list_keyboard,
)
from app.bot.states import AdminUserStates
from app.core.admin_access import ensure_db_admin
from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, NotFoundError
from app.repositories.user_repository import UserRepository
from app.schemas.admin import AdminUserUpdateRequest
from app.services.admin_service import AdminService

router = Router(name="admin_users")
router.message.filter(AdminFilter())

BOT_USERS_PAGE_SIZE = 8


async def _send_admin_menu_to(telegram_id: int, bot) -> None:
    """Push admin reply keyboard after role=admin is granted in DB."""
    url = get_settings().telegram_webapp_url
    if not url.startswith("https://"):
        return
    try:
        await bot.send_message(
            telegram_id,
            "<b>Вам выдана роль администратора.</b>\n\n"
            "Кнопки управления внизу: статистика, персонажи, рассылка, промокоды, товары.",
            reply_markup=main_reply_keyboard(url, include_admin=True),
        )
    except Exception:
        pass


class UserListButtonFilter(BaseFilter):
    async def __call__(self, message: Message, state: FSMContext) -> bool:
        text = message.text
        if not text:
            return False
        data = await state.get_data()
        return text in data.get("user_btn_map", {})


async def _admin_id(telegram_id: int) -> UUID | None:
    async with bot_session() as session:
        repo = UserRepository(session)
        user = await repo.get_by_telegram_id(telegram_id)
        if not user:
            return None
        if await ensure_db_admin(user, repo):
            return user.id
    return None


async def _answer_admin_error(message: Message, exc: Exception) -> None:
    if isinstance(exc, ForbiddenError):
        await message.answer("Нет прав администратора в базе. Откройте Mini App один раз или проверьте ADMIN_TELEGRAM_USERNAMES.")
    elif isinstance(exc, NotFoundError):
        await message.answer("Пользователь не найден.")
    else:
        await message.answer(f"Ошибка: {exc}")


def _user_btn_label(index: int, user) -> str:
    if user.username:
        name = f"@{user.username}"
    elif user.first_name:
        name = user.first_name
    else:
        name = f"tg:{user.telegram_id}"
    suffix = " 🚫" if user.is_banned else ""
    label = f"👤 {index}. {name}{suffix}"
    return label[:64]


async def _send_users_list(
    message: Message,
    state: FSMContext,
    page: int = 1,
    *,
    search_query: str | None = None,
) -> None:
    admin_id = await _admin_id(message.from_user.id)
    if not admin_id:
        await message.answer("Нет доступа.")
        return

    async with bot_session() as session:
        repo = UserRepository(session)
        if search_query:
            users, total = await repo.search_paginated(
                search_query, page=page, page_size=BOT_USERS_PAGE_SIZE
            )
        else:
            users, total = await repo.list_paginated(page=page, page_size=BOT_USERS_PAGE_SIZE)

    pages = max(1, (total + BOT_USERS_PAGE_SIZE - 1) // BOT_USERS_PAGE_SIZE) if total else 1
    page = min(max(1, page), pages)

    btn_map: dict[str, str] = {}
    labels: list[str] = []
    for i, u in enumerate(users, start=1):
        label = _user_btn_label(i, u)
        btn_map[label] = str(u.id)
        labels.append(label)

    await state.update_data(
        user_btn_map=btn_map,
        users_page=page,
        users_pages=pages,
        users_search_query=search_query or "",
    )

    if search_query:
        header = (
            f"<b>Поиск:</b> <code>{search_query}</code>\n"
            f"Найдено: <b>{total}</b> · стр. {page}/{pages}"
        )
    else:
        header = f"<b>Пользователи</b> · стр. {page}/{pages} · всего {total}"

    if not labels:
        header += "\n\n<i>Никого не найдено.</i>" if search_query else "\n\n<i>Список пуст.</i>"

    hint = "Выберите пользователя кнопкой ниже."
    if not search_query:
        hint += "\nИли нажмите «🔍 Поиск пользователей»."

    await message.answer(
        header + f"\n\n{hint}",
        reply_markup=users_list_keyboard(
            labels,
            page=page,
            pages=pages,
            search_active=bool(search_query),
        ),
    )


def _format_user_detail(detail, stats) -> str:
    name = " ".join(filter(None, [detail.first_name, detail.last_name])) or "Без имени"
    uname = f"@{detail.username}" if detail.username else f"tg:{detail.telegram_id}"
    ban = "да 🚫" if detail.is_banned else "нет"
    active = "да" if detail.is_active else "нет"
    return (
        f"<b>{name}</b>\n"
        f"{uname} · роль <b>{detail.role}</b>\n"
        f"Бан: <b>{ban}</b> · активен: <b>{active}</b>\n"
        f"💎 {detail.gems} · кредиты {detail.credits} · потрачено {detail.total_spent}\n\n"
        f"<b>Активность</b>\n"
        f"Чаты: <b>{stats.chats_count}</b> · сообщения: <b>{stats.messages_count}</b>\n"
        f"Генерации: <b>{stats.generations_total}</b> (готово {stats.generations_completed})\n"
        f"Покупок: <b>{stats.purchases_completed}</b> · Stars: <b>{stats.stars_spent_total}</b>"
    )


async def _send_user_detail(message: Message, state: FSMContext, user_id: UUID) -> None:
    admin_id = await _admin_id(message.from_user.id)
    if not admin_id:
        return

    async with bot_session() as session:
        svc = AdminService(session)
        try:
            detail = await svc.get_user(admin_id, user_id)
            stats = await svc.get_user_stats(admin_id, user_id)
        except NotFoundError:
            await message.answer("Пользователь не найден.")
            await _send_users_list(message, state, page=(await state.get_data()).get("users_page", 1))
            return

    await state.update_data(selected_user_id=str(user_id))
    await state.set_state(None)
    text = _format_user_detail(detail, stats)
    await message.answer(
        text,
        reply_markup=user_detail_keyboard(is_banned=detail.is_banned),
    )


@router.message(F.text == ADMIN_MENU_TEXT_USERS)
async def admin_users_open(message: Message, state: FSMContext) -> None:
    await state.set_state(None)
    await _send_users_list(message, state, page=1, search_query=None)


@router.message(F.text == ADMIN_USERS_SEARCH)
async def admin_users_search_start(message: Message, state: FSMContext) -> None:
    await state.set_state(AdminUserStates.search)
    await message.answer(
        "<b>Поиск пользователей</b>\n\n"
        "Введите <b>username</b> (с @ или без), <b>имя</b>, <b>фамилию</b> "
        "или <b>Telegram ID</b> (число):\n\n"
        "<i>Отмена: /cancel</i>",
        reply_markup=users_list_keyboard([], page=1, pages=1, search_active=False),
    )


@router.message(F.text == ADMIN_USERS_CLEAR_SEARCH)
async def admin_users_search_clear(message: Message, state: FSMContext) -> None:
    await state.set_state(None)
    await _send_users_list(message, state, page=1, search_query=None)


@router.message(AdminUserStates.search)
async def admin_users_search_run(message: Message, state: FSMContext) -> None:
    query = (message.text or "").strip()
    if not query:
        await message.answer("Введите непустой запрос для поиска.")
        return
    await state.set_state(None)
    await _send_users_list(message, state, page=1, search_query=query)


@router.message(F.text == ADMIN_MENU_TEXT_BACK_STATS)
async def admin_users_back_stats(message: Message, state: FSMContext) -> None:
    from app.bot.handlers.admin import _send_stats

    await state.set_state(None)
    await _send_stats(message, message.from_user)


@router.message(F.text == ADMIN_MENU_TEXT_BACK_USERS)
async def admin_users_back_list(message: Message, state: FSMContext) -> None:
    await state.set_state(None)
    data = await state.get_data()
    q = (data.get("users_search_query") or "").strip() or None
    await _send_users_list(message, state, page=data.get("users_page", 1), search_query=q)


@router.message(F.text == ADMIN_MENU_TEXT_BACK_USER)
async def admin_users_back_detail(message: Message, state: FSMContext) -> None:
    await state.set_state(None)
    data = await state.get_data()
    uid = data.get("selected_user_id")
    if uid:
        await _send_user_detail(message, state, UUID(uid))
    else:
        await _send_users_list(message, state, page=data.get("users_page", 1))


@router.message(F.text.in_({ADMIN_USERS_PAGE_PREV, ADMIN_USERS_PAGE_NEXT}))
async def admin_users_page(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    page = int(data.get("users_page", 1))
    pages = int(data.get("users_pages", 1))
    if message.text == ADMIN_USERS_PAGE_PREV:
        page = max(1, page - 1)
    else:
        page = min(pages, page + 1)
    q = (data.get("users_search_query") or "").strip() or None
    await _send_users_list(message, state, page=page, search_query=q)


@router.message(UserListButtonFilter())
async def admin_user_pick(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    user_id = UUID(data["user_btn_map"][message.text])
    await _send_user_detail(message, state, user_id)


@router.message(F.text.in_({ADMIN_USER_BLOCK, ADMIN_USER_UNBLOCK}))
async def admin_user_toggle_ban(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    uid = data.get("selected_user_id")
    if not uid:
        await message.answer("Сначала выберите пользователя из списка.")
        return

    admin_id = await _admin_id(message.from_user.id)
    if not admin_id:
        return

    ban = message.text == ADMIN_USER_BLOCK
    try:
        async with bot_session() as session:
            await AdminService(session).set_user_ban(admin_id, UUID(uid), ban)
    except (ForbiddenError, NotFoundError) as exc:
        await _answer_admin_error(message, exc)
        return
    except Exception as exc:
        await _answer_admin_error(message, exc)
        return

    action = "заблокирован" if ban else "разблокирован"
    await message.answer(f"Пользователь {action}.")
    await _send_user_detail(message, state, UUID(uid))


@router.message(F.text == ADMIN_USER_EDIT_MENU)
async def admin_user_edit_menu(message: Message, state: FSMContext) -> None:
    if not (await state.get_data()).get("selected_user_id"):
        await message.answer("Сначала выберите пользователя.")
        return
    await state.set_state(None)
    await message.answer(
        "<b>Редактирование</b>\n\nВыберите поле или смените роль одной кнопкой.",
        reply_markup=user_edit_keyboard(),
    )


@router.message(F.text == ADMIN_USER_TOGGLE_ROLE)
async def admin_user_toggle_role(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    uid = data.get("selected_user_id")
    if not uid:
        return

    admin_id = await _admin_id(message.from_user.id)
    if not admin_id:
        return

    user_id = UUID(uid)
    new_role = "admin"
    target_tg_id = 0
    try:
        async with bot_session() as session:
            svc = AdminService(session)
            detail = await svc.get_user(admin_id, user_id)
            target_tg_id = detail.telegram_id
            new_role = "user" if detail.role == "admin" else "admin"
            await svc.update_user(admin_id, user_id, AdminUserUpdateRequest(role=new_role))
    except (ForbiddenError, NotFoundError) as exc:
        await _answer_admin_error(message, exc)
        return
    except Exception as exc:
        await _answer_admin_error(message, exc)
        return

    await message.answer(f"Роль изменена на <b>{new_role}</b>.")
    if new_role == "admin" and target_tg_id:
        await _send_admin_menu_to(target_tg_id, message.bot)
        await message.answer(
            "Пользователю отправлено уведомление с админ-кнопками. "
            "Если не пришло — пусть напишет /start."
        )
    await _send_user_detail(message, state, user_id)


@router.message(F.text == ADMIN_USER_EDIT_NAME)
async def admin_user_edit_name_start(message: Message, state: FSMContext) -> None:
    if not (await state.get_data()).get("selected_user_id"):
        return
    await state.set_state(AdminUserStates.edit_name)
    await message.answer("Введите новое <b>имя</b> (first_name):")


@router.message(F.text == ADMIN_USER_EDIT_GEMS)
async def admin_user_edit_gems_start(message: Message, state: FSMContext) -> None:
    if not (await state.get_data()).get("selected_user_id"):
        return
    await state.set_state(AdminUserStates.edit_gems)
    await message.answer("Введите новый баланс <b>гемов</b> (целое число ≥ 0):")


@router.message(F.text == ADMIN_USER_EDIT_CREDITS)
async def admin_user_edit_credits_start(message: Message, state: FSMContext) -> None:
    if not (await state.get_data()).get("selected_user_id"):
        return
    await state.set_state(AdminUserStates.edit_credits)
    await message.answer("Введите новое число <b>кредитов</b> (целое ≥ 0):")


@router.message(AdminUserStates.edit_name)
async def admin_user_edit_name_save(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Имя не может быть пустым.")
        return
    await _apply_user_update(message, state, AdminUserUpdateRequest(first_name=name))


@router.message(AdminUserStates.edit_gems)
async def admin_user_edit_gems_save(message: Message, state: FSMContext) -> None:
    try:
        gems = int((message.text or "").strip())
        if gems < 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите целое число ≥ 0.")
        return
    await _apply_user_update(message, state, AdminUserUpdateRequest(gems=gems))


@router.message(AdminUserStates.edit_credits)
async def admin_user_edit_credits_save(message: Message, state: FSMContext) -> None:
    try:
        credits = int((message.text or "").strip())
        if credits < 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите целое число ≥ 0.")
        return
    await _apply_user_update(message, state, AdminUserUpdateRequest(credits=credits))


async def _apply_user_update(
    message: Message, state: FSMContext, body: AdminUserUpdateRequest
) -> None:
    data = await state.get_data()
    uid = data.get("selected_user_id")
    if not uid:
        await state.set_state(None)
        return

    admin_id = await _admin_id(message.from_user.id)
    if not admin_id:
        return

    user_id = UUID(uid)
    try:
        async with bot_session() as session:
            await AdminService(session).update_user(admin_id, user_id, body)
    except (ForbiddenError, NotFoundError) as exc:
        await _answer_admin_error(message, exc)
        return
    except Exception as exc:
        await _answer_admin_error(message, exc)
        return

    await state.set_state(None)
    await message.answer("Сохранено.")
    await _send_user_detail(message, state, user_id)


@router.message(F.text == ADMIN_MENU_TEXT_BACK_ADMIN)
async def admin_users_back_main(message: Message, state: FSMContext) -> None:
    from app.bot.handlers.admin import _admin_start_markup, _admin_start_text

    await state.clear()
    await message.answer(_admin_start_text(), reply_markup=_admin_start_markup())
