from aiogram.fsm.state import State, StatesGroup


class AdminArtStates(StatesGroup):
    title = State()
    description = State()
    photo = State()
    edit_title = State()
    edit_description = State()
    edit_photo = State()


class AdminPromoStates(StatesGroup):
    name = State()
    discount = State()
    code = State()
    max_uses = State()
    edit_max_uses = State()


class AdminBroadcastStates(StatesGroup):
    message = State()
    confirm = State()


class AdminProductStates(StatesGroup):
    name = State()
    product_type = State()
    price = State()
    sale_price = State()
    gems_amount = State()
    credits_amount = State()
    photo = State()
    edit_photo = State()
