from aiogram.fsm.state import State, StatesGroup


class AdminCharacterStates(StatesGroup):
    name = State()
    name_alt = State()
    description = State()
    description_alt = State()
    subtitle = State()
    subtitle_alt = State()
    behavior_param = State()
    behavior_param_alt = State()
    photo = State()
    edit_name = State()
    edit_name_alt = State()
    edit_description = State()
    edit_description_alt = State()
    edit_subtitle = State()
    edit_subtitle_alt = State()
    edit_photo = State()
    scenario_title = State()
    scenario_title_alt = State()
    scenario_story = State()
    scenario_communication = State()
    scenario_opening = State()
    narrator_name = State()
    narrator_name_alt = State()
    narrator_description = State()
    narrator_price = State()


class AdminScenarioStates(StatesGroup):
    title = State()
    story = State()
    communication_style = State()
    opening_message = State()
    photo = State()


class AdminNarratorStates(StatesGroup):
    name = State()
    description = State()
    price = State()
    edit_price = State()
    photo = State()


class AdminPromoStates(StatesGroup):
    name = State()
    discount = State()
    code = State()
    max_uses = State()
    edit_max_uses = State()


class AdminBroadcastStates(StatesGroup):
    message = State()
    message_alt = State()
    confirm = State()


class AdminUserStates(StatesGroup):
    search = State()
    edit_name = State()
    edit_gems = State()
    edit_credits = State()
    ban_duration = State()
    ban_reason = State()


class AdminTopupStates(StatesGroup):
    search = State()


class AdminProductStates(StatesGroup):
    name = State()
    name_alt = State()
    product_type = State()
    price = State()
    sale_price = State()
    gems_amount = State()
    credits_amount = State()
    photo = State()
    edit_photo = State()
