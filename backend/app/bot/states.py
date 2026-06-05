from aiogram.fsm.state import State, StatesGroup


class AdminCharacterStates(StatesGroup):
    name = State()
    description = State()
    subtitle = State()
    behavior_param = State()
    photo = State()
    scenario_title = State()
    scenario_story = State()
    scenario_communication = State()
    scenario_opening = State()
    narrator_name = State()
    narrator_description = State()


class AdminScenarioStates(StatesGroup):
    title = State()
    story = State()
    communication_style = State()
    opening_message = State()


class AdminNarratorStates(StatesGroup):
    name = State()
    description = State()
    price = State()


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
