from uuid import UUID

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.db import bot_session
from app.bot.filters import AdminFilter
from app.bot.keyboards import (
    ADMIN_MENU_TEXT_CHARACTERS,
    ADMIN_MENU_TEXT_CHAR_DELETE,
    ADMIN_MENU_TEXT_CHAR_NEW,
    ADMIN_MENU_TEXT_CHAR_ORDER,
    cancel_kb,
    char_create_scenario_kb,
    char_create_narrator_kb,
    character_delete_confirm_menu,
    character_delete_list_menu,
    character_item_menu,
    character_order_controls_menu,
    character_order_list_menu,
    characters_menu,
    characters_submenu_keyboard,
    scenario_item_menu,
    scenarios_menu,
    narrators_menu,
    narrator_item_menu,
)
from app.bot.states import AdminCharacterStates, AdminNarratorStates, AdminScenarioStates
from app.bot.utils import upload_telegram_photo
from app.core.exceptions import NotFoundError, ValidationError
from app.repositories.user_repository import UserRepository
from app.services.bot_character_service import BEHAVIOR_PARAMS_COUNT, BotCharacterService

router = Router(name="admin_characters")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


async def _admin_id(telegram_id: int) -> UUID | None:
    from app.core.admin_access import ensure_db_admin

    async with bot_session() as session:
        repo = UserRepository(session)
        user = await repo.get_by_telegram_id(telegram_id)
        if not user:
            return None
        if await ensure_db_admin(user, repo):
            return user.id
    return None


def _format_character(ch) -> str:
    params = ch.behavior_params or []
    params_text = "\n".join(f"  {i + 1}. {p}" for i, p in enumerate(params)) or "  —"
    subtitle = f"\nПодпись: <b>{ch.subtitle}</b>" if ch.subtitle else ""
    photo = f"\nФото: {ch.avatar_url}" if ch.avatar_url else "\nФото: нет"
    return (
        f"<b>{ch.name}</b>{subtitle}\n\n"
        f"<b>Описание</b> ({len(ch.description)}/{500}):\n{ch.description}\n\n"
        f"<b>Параметры поведения</b> (для нейросети):\n{params_text}\n\n"
        f"<b>System prompt:</b>\n<code>{(ch.personality_prompt or '—')[:800]}</code>"
        f"{photo}"
    )


def _format_scenario(sc) -> str:
    photo = f"\n\nФото: {sc.image_url}" if sc.image_url else "\n\nФото: нет"
    return (
        f"<b>{sc.title}</b>\n\n"
        f"<b>История / контекст</b>\n{sc.story or '—'}\n\n"
        f"<b>Тип общения в диалоге</b>\n{sc.communication_style or '—'}\n\n"
        f"<b>Стартовое сообщение</b>\n{sc.opening_message or '—'}"
        f"{photo}"
    )


def _format_catalog_order(catalog: list) -> str:
    if not catalog:
        return "<i>В каталоге на главной пока никого нет.</i>"
    lines = []
    for i, ch in enumerate(catalog, start=1):
        sub = f" — {ch.subtitle}" if ch.subtitle else ""
        lines.append(f"{i}. <b>{ch.name}</b>{sub}")
    return "\n".join(lines)


def _characters_list_text(*, extra: str = "", empty: bool = False) -> str:
    text = (
        "<b>Персонажи</b>\n\n"
        "Цифра у имени — место на главной в Mini App.\n"
        "Кнопки внизу: новый, порядок, удаление.\n"
        "Нажмите имя в списке, чтобы открыть карточку."
    )
    if extra:
        text += f"\n\n{extra}"
    if empty:
        text += "\n\n<i>Активных персонажей нет.</i>"
    return text


async def _load_characters_list() -> tuple[list, dict]:
    async with bot_session() as session:
        svc = BotCharacterService(session)
        chars, _ = await svc.list_characters()
        positions = await svc.catalog_positions()
    return chars, positions


async def _send_characters_list(message: Message, *, extra: str = "") -> None:
    chars, positions = await _load_characters_list()
    text = _characters_list_text(extra=extra, empty=not chars)
    await message.answer("Раздел персонажей", reply_markup=characters_submenu_keyboard())
    await message.answer(text, reply_markup=characters_menu(chars, positions))


async def _edit_characters_list(message: Message, *, extra: str = "") -> None:
    chars, positions = await _load_characters_list()
    text = _characters_list_text(extra=extra, empty=not chars)
    try:
        await message.edit_text(text, reply_markup=characters_menu(chars, positions))
    except Exception:
        await message.answer(text, reply_markup=characters_menu(chars, positions))


async def _send_order_list(message: Message, *, edit: bool = False) -> None:
    async with bot_session() as session:
        catalog = await BotCharacterService(session).list_catalog()
    text = (
        "<b>Порядок на главной</b>\n\n"
        "Первый в списке — первая карточка в каталоге Mini App.\n\n"
        f"{_format_catalog_order(catalog)}"
    )
    markup = character_order_list_menu(catalog)
    if edit:
        await message.edit_text(text, reply_markup=markup)
    else:
        await message.answer(text, reply_markup=markup)


async def _send_order_controls(message: Message, char_id: UUID, *, edit: bool = True) -> None:
    async with bot_session() as session:
        svc = BotCharacterService(session)
        ch = await svc.get_character(char_id)
        catalog = await svc.list_catalog()
        positions = await svc.catalog_positions()
    pos = positions.get(char_id)
    if pos is None:
        text = (
            f"<b>{ch.name}</b> не в каталоге на главной "
            "(скрыт или неактивен)."
        )
        markup = character_item_menu(str(char_id))
    else:
        sub = f"\nПодпись: <b>{ch.subtitle}</b>" if ch.subtitle else ""
        text = (
            f"<b>{ch.name}</b>{sub}\n\n"
            f"Позиция на главной: <b>{pos}</b> из {len(catalog)}"
        )
        markup = character_order_controls_menu(str(char_id), pos, len(catalog))
    if edit:
        await message.edit_text(text, reply_markup=markup)
    else:
        await message.answer(text, reply_markup=markup)


@router.message(F.text == ADMIN_MENU_TEXT_CHARACTERS)
async def admin_chars_reply(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _send_characters_list(message)


@router.message(F.text == ADMIN_MENU_TEXT_CHAR_NEW)
async def admin_char_new_reply(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AdminCharacterStates.name)
    await state.update_data(behavior_params=[])
    await message.answer(
        "<b>Создание персонажа</b>\n\n"
        "1/6 Введите <b>имя</b> (например: Акира):",
        reply_markup=cancel_kb("adm:chars"),
    )


@router.message(F.text == ADMIN_MENU_TEXT_CHAR_ORDER)
async def admin_char_order_reply(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _send_order_list(message, edit=False)


@router.message(F.text == ADMIN_MENU_TEXT_CHAR_DELETE)
async def admin_char_delete_reply(message: Message, state: FSMContext) -> None:
    await state.clear()
    async with bot_session() as session:
        chars, _ = await BotCharacterService(session).list_characters()
    active = [ch for ch in chars if ch.is_active and not ch.is_hidden]
    text = "<b>Удаление персонажа</b>\n\nВыберите, кого убрать с главной в Mini App."
    if not active:
        text += "\n\n<i>Активных персонажей нет.</i>"
    await message.answer(text, reply_markup=character_delete_list_menu(chars))


@router.callback_query(F.data == "adm:chars")
async def admin_chars_list_cb(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Раздел персонажей", reply_markup=characters_submenu_keyboard())
    async with bot_session() as session:
        svc = BotCharacterService(session)
        chars, _ = await svc.list_characters()
        positions = await svc.catalog_positions()
    text = (
        "<b>Персонажи</b>\n\n"
        "Цифра у имени — место на главной в Mini App.\n"
        "Кнопки внизу: новый, порядок, удаление."
    )
    if not chars:
        text += "\n\n<i>Список пуст.</i>"
    await callback.message.answer(text, reply_markup=characters_menu(chars, positions))
    await callback.answer()


@router.callback_query(F.data == "adm:char:add")
async def admin_char_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AdminCharacterStates.name)
    await state.update_data(behavior_params=[])
    await callback.message.edit_text(
        "<b>Создание персонажа</b>\n\n"
        "1/6 Введите <b>имя</b> (например: Акира):",
        reply_markup=cancel_kb("adm:chars"),
    )
    await callback.answer()


@router.message(AdminCharacterStates.name)
async def admin_char_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Имя не может быть пустым.")
        return
    await state.update_data(name=name)
    await state.set_state(AdminCharacterStates.description)
    await message.answer(
        "2/6 <b>Описание</b> персонажа (до 500 символов):",
        reply_markup=cancel_kb("adm:chars"),
    )


@router.message(AdminCharacterStates.description)
async def admin_char_description(message: Message, state: FSMContext) -> None:
    desc = (message.text or "").strip()
    if not desc:
        await message.answer("Описание не может быть пустым.")
        return
    if len(desc) > 500:
        await message.answer(f"Слишком длинно: {len(desc)}/500. Сократите текст.")
        return
    await state.update_data(description=desc)
    await state.set_state(AdminCharacterStates.subtitle)
    await message.answer(
        "3/6 <b>Подпись под именем</b> (например: «Милая девочка»):\n"
        "<i>Отображается под именем на карточке.</i>",
        reply_markup=cancel_kb("adm:chars"),
    )


@router.message(AdminCharacterStates.subtitle)
async def admin_char_subtitle(message: Message, state: FSMContext) -> None:
    await state.update_data(subtitle=(message.text or "").strip())
    await state.update_data(behavior_param_index=1)
    await state.set_state(AdminCharacterStates.behavior_param)
    await message.answer(
        f"4/6 <b>Параметр поведения 1/{BEHAVIOR_PARAMS_COUNT}</b>\n"
        "Краткая черта для нейросети (тон, характер, стиль речи):",
        reply_markup=cancel_kb("adm:chars"),
    )


@router.message(AdminCharacterStates.behavior_param)
async def admin_char_behavior_param(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    idx = int(data.get("behavior_param_index", 1))
    params: list[str] = list(data.get("behavior_params", []))
    text = (message.text or "").strip()
    if not text:
        await message.answer("Параметр не может быть пустым.")
        return
    params.append(text)
    await state.update_data(behavior_params=params)
    if idx >= BEHAVIOR_PARAMS_COUNT:
        await state.set_state(AdminCharacterStates.photo)
        await message.answer(
            "5/6 Отправьте <b>фото</b> персонажа (или /skip):",
            reply_markup=cancel_kb("adm:chars"),
        )
        return
    next_idx = idx + 1
    await state.update_data(behavior_param_index=next_idx)
    await message.answer(
        f"4/6 <b>Параметр поведения {next_idx}/{BEHAVIOR_PARAMS_COUNT}</b>:",
        reply_markup=cancel_kb("adm:chars"),
    )


@router.message(AdminCharacterStates.photo, Command("skip"))
async def admin_char_photo_skip(message: Message, state: FSMContext) -> None:
    await _save_new_character(message, state, avatar_url=None)


@router.message(AdminCharacterStates.photo, F.photo)
async def admin_char_photo(message: Message, state: FSMContext, bot: Bot) -> None:
    try:
        avatar_url = await upload_telegram_photo(bot, message.photo[-1].file_id)
    except Exception as exc:
        await message.answer(f"Не удалось загрузить фото: {exc}")
        return
    await _save_new_character(message, state, avatar_url=avatar_url)


async def _start_scenario_wizard(message: Message, state: FSMContext, char_id: UUID, *, scenario_num: int) -> None:
    await state.update_data(created_character_id=str(char_id), scenario_num=scenario_num)
    await state.set_state(AdminCharacterStates.scenario_title)
    await message.answer(
        f"<b>Персонаж сохранён.</b> Сценарий <b>{scenario_num}</b>\n\n"
        "1/4 <b>Название</b> сценария (как в Mini App, например: «Новое знакомство»):",
        reply_markup=cancel_kb("adm:chars"),
    )


async def _save_new_character(message: Message, state: FSMContext, avatar_url: str | None) -> None:
    data = await state.get_data()
    admin_id = await _admin_id(message.from_user.id)
    if not admin_id:
        await message.answer("Нет прав администратора.")
        return
    try:
        async with bot_session() as session:
            ch = await BotCharacterService(session).create_character(
                admin_id,
                name=data["name"],
                description=data["description"],
                subtitle=data.get("subtitle", ""),
                behavior_params=data.get("behavior_params", []),
                avatar_url=avatar_url,
            )
    except ValidationError as exc:
        await message.answer(str(exc.message))
        return
    except Exception as exc:
        await message.answer(f"Ошибка: {exc}")
        return

    sub = f"\nПодпись: <b>{ch.subtitle}</b>" if ch.subtitle else ""
    await message.answer(
        f"Персонаж <b>{ch.name}</b> на <b>1-м месте</b> в каталоге.{sub}\n\n"
        "Теперь добавьте хотя бы один сценарий и рассказчика для кнопки «Играть».",
    )
    await _start_scenario_wizard(message, state, ch.id, scenario_num=1)


@router.message(AdminCharacterStates.scenario_title)
async def admin_char_create_scenario_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer("Название сценария обязательно.")
        return
    await state.update_data(scenario_title=title)
    await state.set_state(AdminCharacterStates.scenario_story)
    await message.answer(
        "2/4 <b>История / контекст</b> сценария:",
        reply_markup=cancel_kb("adm:chars"),
    )


@router.message(AdminCharacterStates.scenario_story)
async def admin_char_create_scenario_story(message: Message, state: FSMContext) -> None:
    await state.update_data(scenario_story=(message.text or "").strip())
    await state.set_state(AdminCharacterStates.scenario_communication)
    await message.answer(
        "3/4 <b>Тип общения</b> в диалоге (флирт, дружеский, таинственный…):",
        reply_markup=cancel_kb("adm:chars"),
    )


@router.message(AdminCharacterStates.scenario_communication)
async def admin_char_create_scenario_communication(message: Message, state: FSMContext) -> None:
    await state.update_data(scenario_communication=(message.text or "").strip())
    await state.set_state(AdminCharacterStates.scenario_opening)
    await message.answer(
        "4/4 <b>Стартовое сообщение</b> персонажа (или /skip):",
        reply_markup=cancel_kb("adm:chars"),
    )


@router.message(AdminCharacterStates.scenario_opening, Command("skip"))
async def admin_char_create_scenario_opening_skip(message: Message, state: FSMContext) -> None:
    await _finish_scenario_during_create(message, state, opening_message="")


@router.message(AdminCharacterStates.scenario_opening)
async def admin_char_create_scenario_opening(message: Message, state: FSMContext) -> None:
    await _finish_scenario_during_create(message, state, opening_message=(message.text or "").strip())


async def _finish_scenario_during_create(
    message: Message, state: FSMContext, opening_message: str
) -> None:
    data = await state.get_data()
    admin_id = await _admin_id(message.from_user.id)
    char_id = UUID(data["created_character_id"])
    if not admin_id:
        return
    try:
        async with bot_session() as session:
            sc = await BotCharacterService(session).create_scenario(
                admin_id,
                char_id,
                title=data["scenario_title"],
                story=data.get("scenario_story", ""),
                communication_style=data.get("scenario_communication", ""),
                opening_message=opening_message,
            )
            count = len(await BotCharacterService(session).list_scenarios(char_id))
    except ValidationError as exc:
        await message.answer(str(exc.message))
        return
    except Exception as exc:
        await message.answer(f"Ошибка: {exc}")
        return

    await state.set_state()
    await message.answer(
        f"Сценарий <b>{sc.title}</b> добавлен ({count} всего).\n\n"
        "Добавьте хотя бы один сценарий, затем перейдите к рассказчикам.",
        reply_markup=char_create_scenario_kb(str(char_id), can_finish=True),
    )


async def _start_narrator_wizard(message: Message, state: FSMContext, char_id: UUID, *, narrator_num: int) -> None:
    await state.update_data(created_character_id=str(char_id), narrator_num=narrator_num)
    await state.set_state(AdminCharacterStates.narrator_name)
    await message.answer(
        f"<b>Рассказчик {narrator_num}</b>\n\n"
        "1/3 <b>Название</b> (например: «Классический», «Мистический»):",
        reply_markup=cancel_kb("adm:chars"),
    )


@router.callback_query(F.data.startswith("adm:char:create:narr:start:"))
async def admin_char_create_to_narrators(callback: CallbackQuery, state: FSMContext) -> None:
    char_id = UUID(callback.data.split(":")[-1])
    async with bot_session() as session:
        scenarios = await BotCharacterService(session).list_scenarios(char_id)
    if not scenarios:
        await callback.answer("Сначала добавьте хотя бы один сценарий", show_alert=True)
        return
    await callback.message.edit_text(
        f"Сценариев: <b>{len(scenarios)}</b>. Теперь добавьте рассказчиков для Mini App.",
    )
    await _start_narrator_wizard(callback.message, state, char_id, narrator_num=1)
    await callback.answer()


@router.message(AdminCharacterStates.narrator_name)
async def admin_char_create_narrator_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Название рассказчика обязательно.")
        return
    await state.update_data(narrator_name=name)
    await state.set_state(AdminCharacterStates.narrator_description)
    await message.answer(
        "2/3 <b>Описание</b> рассказчика:",
        reply_markup=cancel_kb("adm:chars"),
    )


@router.message(AdminCharacterStates.narrator_description)
async def admin_char_create_narrator_description(message: Message, state: FSMContext) -> None:
    await state.update_data(narrator_description=(message.text or "").strip())
    await state.set_state(AdminCharacterStates.narrator_price)
    await message.answer(
        "3/3 <b>Цена в сердцах</b> за сообщение (число, 0 = 1 сердце):",
        reply_markup=cancel_kb("adm:chars"),
    )


@router.message(AdminCharacterStates.narrator_price)
async def admin_char_create_narrator_price(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("Введите число (0 или больше).")
        return
    await _finish_narrator_during_create(message, state, price=int(raw))


async def _finish_narrator_during_create(message: Message, state: FSMContext, price: int) -> None:
    data = await state.get_data()
    admin_id = await _admin_id(message.from_user.id)
    char_id = UUID(data["created_character_id"])
    if not admin_id:
        return
    try:
        async with bot_session() as session:
            narrator = await BotCharacterService(session).create_narrator(
                admin_id,
                char_id,
                name=data["narrator_name"],
                description=data.get("narrator_description", ""),
                price=price,
            )
            count = len(await BotCharacterService(session).list_narrators(char_id))
    except ValidationError as exc:
        await message.answer(str(exc.message))
        return
    except Exception as exc:
        await message.answer(f"Ошибка: {exc}")
        return

    await state.set_state()
    await message.answer(
        f"Рассказчик <b>{narrator.name}</b> добавлен ({count} всего).",
        reply_markup=char_create_narrator_kb(str(char_id), can_finish=True),
    )


@router.callback_query(F.data.startswith("adm:char:create:narr:more:"))
async def admin_char_create_narrator_more(callback: CallbackQuery, state: FSMContext) -> None:
    char_id = UUID(callback.data.split(":")[-1])
    data = await state.get_data()
    next_num = int(data.get("narrator_num", 1)) + 1
    await state.update_data(narrator_num=next_num)
    await _start_narrator_wizard(callback.message, state, char_id, narrator_num=next_num)
    await callback.answer()


@router.callback_query(F.data.startswith("adm:char:create:scen:more:"))
async def admin_char_create_scenario_more(callback: CallbackQuery, state: FSMContext) -> None:
    char_id = UUID(callback.data.split(":")[-1])
    data = await state.get_data()
    next_num = int(data.get("scenario_num", 1)) + 1
    await state.update_data(scenario_num=next_num)
    await _start_scenario_wizard(callback.message, state, char_id, scenario_num=next_num)
    await callback.answer()


@router.callback_query(F.data.startswith("adm:char:create:done:"))
async def admin_char_create_done(callback: CallbackQuery, state: FSMContext) -> None:
    char_id = UUID(callback.data.split(":")[-1])
    async with bot_session() as session:
        ch = await BotCharacterService(session).get_character(char_id)
        scenarios = await BotCharacterService(session).list_scenarios(char_id)
        narrators = await BotCharacterService(session).list_narrators(char_id)
    if not scenarios:
        await callback.answer("Нужен хотя бы один сценарий", show_alert=True)
        return
    if not narrators:
        await callback.answer("Нужен хотя бы один рассказчик", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text(
        f"<b>{ch.name}</b> полностью создан.\n"
        f"Сценариев: <b>{len(scenarios)}</b>, рассказчиков: <b>{len(narrators)}</b>.\n"
        "Карточка и «Играть» готовы в Mini App.",
        reply_markup=character_item_menu(str(char_id)),
    )
    await callback.answer("Готово")


@router.callback_query(F.data == "adm:char:delete")
async def admin_char_delete_list(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    async with bot_session() as session:
        chars, _ = await BotCharacterService(session).list_characters()
    active = [ch for ch in chars if ch.is_active and not ch.is_hidden]
    text = "<b>Удаление персонажа</b>\n\nВыберите, кого убрать с главной в Mini App."
    if not active:
        text += "\n\n<i>Активных персонажей нет.</i>"
    await callback.message.edit_text(text, reply_markup=character_delete_list_menu(chars))
    await callback.answer()


@router.callback_query(F.data.startswith("adm:char:del:ask:"))
async def admin_char_delete_confirm(callback: CallbackQuery) -> None:
    char_id = UUID(callback.data.split(":")[-1])
    async with bot_session() as session:
        ch = await BotCharacterService(session).get_character(char_id)
    sub = f"\nПодпись: <b>{ch.subtitle}</b>" if ch.subtitle else ""
    await callback.message.edit_text(
        f"Удалить персонажа <b>{ch.name}</b>?{sub}\n\n"
        "Он исчезнет из каталога Mini App. Сценарии останутся в базе, но будут скрыты.",
        reply_markup=character_delete_confirm_menu(str(char_id)),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm:char:del:yes:"))
async def admin_char_delete_do(callback: CallbackQuery, state: FSMContext) -> None:
    char_id = UUID(callback.data.split(":")[-1])
    admin_id = await _admin_id(callback.from_user.id)
    if not admin_id:
        await callback.answer("Нет прав", show_alert=True)
        return
    name = ""
    try:
        async with bot_session() as session:
            ch = await BotCharacterService(session).delete_character(admin_id, char_id)
            name = ch.name
    except ValidationError as exc:
        await callback.answer(str(exc.message), show_alert=True)
        return
    except NotFoundError:
        await callback.answer("Не найден", show_alert=True)
        return
    except Exception as exc:
        await callback.answer(f"Ошибка: {exc}", show_alert=True)
        return

    await state.clear()
    await callback.answer(f"{name} удалён")
    await _edit_characters_list(
        callback.message,
        extra=f"Персонаж <b>{name}</b> удалён.",
    )


@router.callback_query(F.data == "adm:char:order")
async def admin_char_order_list(callback: CallbackQuery) -> None:
    await _send_order_list(callback.message, edit=True)
    await callback.answer()


@router.callback_query(F.data.startswith("adm:char:order:view:"))
async def admin_char_order_view(callback: CallbackQuery) -> None:
    char_id = UUID(callback.data.split(":")[-1])
    await _send_order_controls(callback.message, char_id)
    await callback.answer()


@router.callback_query(F.data.regexp(r"^adm:char:order:(up|down|top):"))
async def admin_char_order_move(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    direction = parts[3]
    char_id = UUID(parts[4])
    admin_id = await _admin_id(callback.from_user.id)
    if not admin_id:
        await callback.answer("Нет прав", show_alert=True)
        return
    try:
        async with bot_session() as session:
            moved, new_pos = await BotCharacterService(session).move_catalog_character(
                admin_id, char_id, direction
            )
    except ValidationError as exc:
        await callback.answer(str(exc.message), show_alert=True)
        return
    if not moved:
        await callback.answer("Уже на этой позиции")
        return
    await callback.answer(f"Позиция: {new_pos}")
    await _send_order_controls(callback.message, char_id)


@router.callback_query(F.data.startswith("adm:char:view:"))
async def admin_char_view(callback: CallbackQuery) -> None:
    char_id = UUID(callback.data.split(":")[-1])
    async with bot_session() as session:
        ch = await BotCharacterService(session).get_character(char_id)
    await callback.message.edit_text(
        _format_character(ch),
        reply_markup=character_item_menu(str(ch.id)),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm:char:scenarios:"))
async def admin_char_scenarios_list(callback: CallbackQuery) -> None:
    char_id = UUID(callback.data.split(":")[-1])
    async with bot_session() as session:
        svc = BotCharacterService(session)
        ch = await svc.get_character(char_id)
        scenarios = await svc.list_scenarios(char_id)
    text = f"<b>Сценарии</b> — {ch.name}\n\nВыберите или создайте новый."
    if not scenarios:
        text += "\n\n<i>Сценариев пока нет.</i>"
    await callback.message.edit_text(text, reply_markup=scenarios_menu(str(char_id), scenarios))
    await callback.answer()


@router.callback_query(F.data.startswith("adm:scen:add:"))
async def admin_scenario_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    char_id = callback.data.split(":")[-1]
    await state.set_state(AdminScenarioStates.title)
    await state.update_data(scenario_character_id=char_id)
    await callback.message.edit_text(
        "<b>Новый сценарий</b>\n\n1/4 <b>Название</b> сценария:",
        reply_markup=cancel_kb(f"adm:char:scenarios:{char_id}"),
    )
    await callback.answer()


@router.message(AdminScenarioStates.title)
async def admin_scenario_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer("Название обязательно.")
        return
    await state.update_data(scenario_title=title)
    await state.set_state(AdminScenarioStates.story)
    data = await state.get_data()
    await message.answer(
        "2/4 <b>История / контекст</b> сценария (что произошло, сеттинг):",
        reply_markup=cancel_kb(f"adm:char:scenarios:{data['scenario_character_id']}"),
    )


@router.message(AdminScenarioStates.story)
async def admin_scenario_story(message: Message, state: FSMContext) -> None:
    await state.update_data(scenario_story=(message.text or "").strip())
    await state.set_state(AdminScenarioStates.communication_style)
    data = await state.get_data()
    await message.answer(
        "3/4 <b>Тип общения</b> в этом диалоге\n"
        "(формальный, флирт, дружеский, таинственный и т.д.):",
        reply_markup=cancel_kb(f"adm:char:scenarios:{data['scenario_character_id']}"),
    )


@router.message(AdminScenarioStates.communication_style)
async def admin_scenario_communication(message: Message, state: FSMContext) -> None:
    await state.update_data(scenario_communication=(message.text or "").strip())
    await state.set_state(AdminScenarioStates.opening_message)
    data = await state.get_data()
    await message.answer(
        "4/4 <b>Стартовое сообщение</b> персонажа в сценарии (или /skip):",
        reply_markup=cancel_kb(f"adm:char:scenarios:{data['scenario_character_id']}"),
    )


@router.message(AdminScenarioStates.opening_message, Command("skip"))
async def admin_scenario_opening_skip(message: Message, state: FSMContext) -> None:
    await _save_new_scenario(message, state, opening_message="")


@router.message(AdminScenarioStates.opening_message)
async def admin_scenario_opening(message: Message, state: FSMContext) -> None:
    await _save_new_scenario(message, state, opening_message=(message.text or "").strip())


async def _save_new_scenario(message: Message, state: FSMContext, opening_message: str) -> None:
    data = await state.get_data()
    admin_id = await _admin_id(message.from_user.id)
    char_id = UUID(data["scenario_character_id"])
    if not admin_id:
        return
    try:
        async with bot_session() as session:
            sc = await BotCharacterService(session).create_scenario(
                admin_id,
                char_id,
                title=data["scenario_title"],
                story=data.get("scenario_story", ""),
                communication_style=data.get("scenario_communication", ""),
                opening_message=opening_message,
            )
    except ValidationError as exc:
        await message.answer(str(exc.message))
        return
    except Exception as exc:
        await message.answer(f"Ошибка: {exc}")
        return

    await state.clear()
    await message.answer(
        f"Сценарий <b>{sc.title}</b> создан.",
        reply_markup=scenario_item_menu(str(sc.id), str(char_id)),
    )


@router.callback_query(F.data.startswith("adm:scen:view:"))
async def admin_scenario_view(callback: CallbackQuery) -> None:
    scenario_id = UUID(callback.data.split(":")[-1])
    async with bot_session() as session:
        from app.repositories.character_scenario_repository import CharacterScenarioRepository

        sc = await CharacterScenarioRepository(session).get_by_id(scenario_id)
        if not sc:
            await callback.answer("Не найден", show_alert=True)
            return
    await callback.message.edit_text(
        _format_scenario(sc),
        reply_markup=scenario_item_menu(str(sc.id), str(sc.character_id)),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm:scen:del:"))
async def admin_scenario_delete(callback: CallbackQuery, state: FSMContext) -> None:
    scenario_id = UUID(callback.data.split(":")[-1])
    admin_id = await _admin_id(callback.from_user.id)
    char_id = None
    if admin_id:
        async with bot_session() as session:
            from app.repositories.character_scenario_repository import CharacterScenarioRepository

            repo = CharacterScenarioRepository(session)
            sc = await repo.get_by_id(scenario_id)
            if sc:
                char_id = sc.character_id
                await BotCharacterService(session).deactivate_scenario(admin_id, scenario_id)
    await callback.answer("Сценарий удалён")
    await state.clear()
    if char_id:
        async with bot_session() as session:
            svc = BotCharacterService(session)
            ch = await svc.get_character(char_id)
            scenarios = await svc.list_scenarios(char_id)
        await callback.message.edit_text(
            f"<b>Сценарии</b> — {ch.name}",
            reply_markup=scenarios_menu(str(char_id), scenarios),
        )


def _format_narrator(narrator) -> str:
    photo = f"\nФото: {narrator.image_url}" if narrator.image_url else "\nФото: нет"
    cost = narrator.price if narrator.price > 0 else 1
    return (
        f"<b>{narrator.name}</b>\n"
        f"Цена за сообщение: <b>{cost}</b> ❤️\n\n"
        f"{(narrator.description or '—').strip()}"
        f"{photo}"
    )


@router.callback_query(F.data.startswith("adm:char:narrators:"))
async def admin_char_narrators_list(callback: CallbackQuery) -> None:
    char_id = UUID(callback.data.split(":")[-1])
    async with bot_session() as session:
        svc = BotCharacterService(session)
        ch = await svc.get_character(char_id)
        narrators = await svc.list_narrators(char_id)
    text = f"<b>Рассказчики</b> — {ch.name}\n\nВыберите или создайте нового."
    if not narrators:
        text += "\n\n<i>Рассказчиков пока нет.</i>"
    await callback.message.edit_text(text, reply_markup=narrators_menu(str(char_id), narrators))
    await callback.answer()


@router.callback_query(F.data.startswith("adm:narr:add:"))
async def admin_narrator_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    char_id = callback.data.split(":")[-1]
    await state.set_state(AdminNarratorStates.name)
    await state.update_data(narrator_character_id=char_id)
    await callback.message.edit_text(
        "<b>Новый рассказчик</b>\n\n1/3 <b>Название</b>:",
        reply_markup=cancel_kb(f"adm:char:narrators:{char_id}"),
    )
    await callback.answer()


@router.message(AdminNarratorStates.name)
async def admin_narrator_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Название обязательно.")
        return
    await state.update_data(narrator_name=name)
    await state.set_state(AdminNarratorStates.description)
    data = await state.get_data()
    await message.answer(
        "2/3 <b>Описание</b> рассказчика:",
        reply_markup=cancel_kb(f"adm:char:narrators:{data['narrator_character_id']}"),
    )


@router.message(AdminNarratorStates.description)
async def admin_narrator_description(message: Message, state: FSMContext) -> None:
    await state.update_data(narrator_description=(message.text or "").strip())
    await state.set_state(AdminNarratorStates.price)
    data = await state.get_data()
    await message.answer(
        "3/3 <b>Цена в сердцах</b> (число, 0 = бесплатно):",
        reply_markup=cancel_kb(f"adm:char:narrators:{data['narrator_character_id']}"),
    )


@router.message(AdminNarratorStates.price)
async def admin_narrator_price(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("Введите число (0 или больше).")
        return
    price = int(raw)
    data = await state.get_data()
    admin_id = await _admin_id(message.from_user.id)
    char_id = UUID(data["narrator_character_id"])
    if not admin_id:
        return
    try:
        async with bot_session() as session:
            narrator = await BotCharacterService(session).create_narrator(
                admin_id,
                char_id,
                name=data["narrator_name"],
                description=data.get("narrator_description", ""),
                price=price,
            )
    except ValidationError as exc:
        await message.answer(str(exc.message))
        return
    except Exception as exc:
        await message.answer(f"Ошибка: {exc}")
        return

    await state.clear()
    await message.answer(
        f"Рассказчик <b>{narrator.name}</b> создан.",
        reply_markup=narrator_item_menu(str(narrator.id), str(char_id)),
    )


@router.callback_query(F.data.startswith("adm:narr:view:"))
async def admin_narrator_view(callback: CallbackQuery) -> None:
    narrator_id = UUID(callback.data.split(":")[-1])
    async with bot_session() as session:
        from app.repositories.character_narrator_repository import CharacterNarratorRepository

        narrator = await CharacterNarratorRepository(session).get_by_id(narrator_id)
        if not narrator:
            await callback.answer("Не найден", show_alert=True)
            return
    await callback.message.edit_text(
        _format_narrator(narrator),
        reply_markup=narrator_item_menu(str(narrator.id), str(narrator.character_id)),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm:narr:price:"))
async def admin_narrator_edit_price_start(callback: CallbackQuery, state: FSMContext) -> None:
    narrator_id = callback.data.split(":")[-1]
    await state.set_state(AdminNarratorStates.edit_price)
    await state.update_data(edit_narrator_id=narrator_id)
    await callback.message.edit_text(
        "<b>Новая цена в сердцах</b> за одно сообщение (0 = 1 сердце):",
        reply_markup=cancel_kb(f"adm:narr:view:{narrator_id}"),
    )
    await callback.answer()


@router.message(AdminNarratorStates.edit_price)
async def admin_narrator_edit_price_save(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("Введите число (0 или больше).")
        return
    data = await state.get_data()
    narrator_id = UUID(data["edit_narrator_id"])
    admin_id = await _admin_id(message.from_user.id)
    if not admin_id:
        return
    try:
        async with bot_session() as session:
            narrator = await BotCharacterService(session).update_narrator(
                admin_id, narrator_id, price=int(raw)
            )
    except Exception as exc:
        await message.answer(f"Ошибка: {exc}")
        return
    await state.clear()
    await message.answer(
        _format_narrator(narrator),
        reply_markup=narrator_item_menu(str(narrator.id), str(narrator.character_id)),
    )


@router.callback_query(F.data.startswith("adm:narr:photo:"))
async def admin_narrator_photo_start(callback: CallbackQuery, state: FSMContext) -> None:
    narrator_id = callback.data.split(":")[-1]
    await state.set_state(AdminNarratorStates.photo)
    await state.update_data(edit_narrator_id=narrator_id)
    await callback.message.edit_text(
        "Отправьте фото рассказчика или /skip чтобы удалить.",
        reply_markup=cancel_kb(f"adm:narr:view:{narrator_id}"),
    )
    await callback.answer()


@router.message(AdminNarratorStates.photo, Command("skip"))
async def admin_narrator_photo_skip(message: Message, state: FSMContext, bot: Bot) -> None:
    await _save_narrator_photo(message, state, bot, image_url=None, clear_image=True)


@router.message(AdminNarratorStates.photo)
async def admin_narrator_photo_save(message: Message, state: FSMContext, bot: Bot) -> None:
    if not message.photo:
        await message.answer("Отправьте фото или /skip")
        return
    image_url = await upload_telegram_photo(bot, message.photo[-1].file_id, prefix="narrators")
    await _save_narrator_photo(message, state, bot, image_url=image_url)


async def _save_narrator_photo(
    message: Message,
    state: FSMContext,
    bot: Bot,
    *,
    image_url: str | None,
    clear_image: bool = False,
) -> None:
    data = await state.get_data()
    narrator_id = UUID(data["edit_narrator_id"])
    admin_id = await _admin_id(message.from_user.id)
    if not admin_id:
        return
    try:
        async with bot_session() as session:
            narrator = await BotCharacterService(session).update_narrator(
                admin_id,
                narrator_id,
                image_url=image_url,
                clear_image=clear_image,
            )
    except Exception as exc:
        await message.answer(f"Ошибка: {exc}")
        return
    await state.clear()
    await message.answer(
        _format_narrator(narrator),
        reply_markup=narrator_item_menu(str(narrator.id), str(narrator.character_id)),
    )


@router.callback_query(F.data.startswith("adm:scen:photo:"))
async def admin_scenario_photo_start(callback: CallbackQuery, state: FSMContext) -> None:
    scenario_id = callback.data.split(":")[-1]
    await state.set_state(AdminScenarioStates.photo)
    await state.update_data(edit_scenario_id=scenario_id)
    await callback.message.edit_text(
        "Отправьте фото сценария или /skip чтобы удалить.",
        reply_markup=cancel_kb(f"adm:scen:view:{scenario_id}"),
    )
    await callback.answer()


@router.message(AdminScenarioStates.photo, Command("skip"))
async def admin_scenario_photo_skip(message: Message, state: FSMContext) -> None:
    await _save_scenario_photo(message, state, image_url=None, clear_image=True)


@router.message(AdminScenarioStates.photo)
async def admin_scenario_photo_save(message: Message, state: FSMContext, bot: Bot) -> None:
    if not message.photo:
        await message.answer("Отправьте фото или /skip")
        return
    image_url = await upload_telegram_photo(bot, message.photo[-1].file_id, prefix="scenarios")
    await _save_scenario_photo(message, state, image_url=image_url)


async def _save_scenario_photo(
    message: Message,
    state: FSMContext,
    *,
    image_url: str | None,
    clear_image: bool = False,
) -> None:
    data = await state.get_data()
    scenario_id = UUID(data["edit_scenario_id"])
    admin_id = await _admin_id(message.from_user.id)
    if not admin_id:
        return
    try:
        async with bot_session() as session:
            scenario = await BotCharacterService(session).update_scenario(
                admin_id,
                scenario_id,
                image_url=image_url,
                clear_image=clear_image,
            )
            char_id = scenario.character_id
    except Exception as exc:
        await message.answer(f"Ошибка: {exc}")
        return
    await state.clear()
    await message.answer(
        _format_scenario(scenario),
        reply_markup=scenario_item_menu(str(scenario.id), str(char_id)),
    )


@router.callback_query(F.data.startswith("adm:narr:del:"))
async def admin_narrator_delete(callback: CallbackQuery, state: FSMContext) -> None:
    narrator_id = UUID(callback.data.split(":")[-1])
    admin_id = await _admin_id(callback.from_user.id)
    char_id = None
    if admin_id:
        async with bot_session() as session:
            from app.repositories.character_narrator_repository import CharacterNarratorRepository

            repo = CharacterNarratorRepository(session)
            narrator = await repo.get_by_id(narrator_id)
            if narrator:
                char_id = narrator.character_id
                await BotCharacterService(session).deactivate_narrator(admin_id, narrator_id)
    await callback.answer("Рассказчик удалён")
    await state.clear()
    if char_id:
        async with bot_session() as session:
            svc = BotCharacterService(session)
            ch = await svc.get_character(char_id)
            narrators = await svc.list_narrators(char_id)
        await callback.message.edit_text(
            f"<b>Рассказчики</b> — {ch.name}",
            reply_markup=narrators_menu(str(char_id), narrators),
        )
