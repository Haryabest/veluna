from aiogram.fsm.state import State, StatesGroup


class AdminCharacterStates(StatesGroup):
    name = State()
    name_en = State()
    description = State()
    description_en = State()
    subtitle = State()
    subtitle_en = State()
    behavior_param = State()
    photo = State()
    edit_name = State()
    edit_description = State()
    edit_subtitle = State()
    edit_photo = State()
    scenario_title = State()
    scenario_title_en = State()
    scenario_story = State()
    scenario_story_en = State()
    scenario_communication = State()
    scenario_communication_en = State()
    scenario_opening = State()
    scenario_opening_en = State()
    narrator_name = State()
    narrator_name_en = State()
    narrator_description = State()
    narrator_description_en = State()
    narrator_price = State()


class AdminScenarioStates(StatesGroup):
    title = State()
    title_en = State()
    story = State()
    story_en = State()
    communication_style = State()
    communication_style_en = State()
    opening_message = State()
    opening_message_en = State()
    photo = State()


class AdminNarratorStates(StatesGroup):
    name = State()
    name_en = State()
    description = State()
    description_en = State()
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
    product_type = State()
    price = State()
    sale_price = State()
    gems_amount = State()
    credits_amount = State()
    photo = State()
    edit_photo = State()
