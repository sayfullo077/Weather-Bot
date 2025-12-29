from aiogram.filters.state import State, StatesGroup


class UserStart(StatesGroup):
    menu = State()
    start = State()
    check = State()


class UserMessageState(StatesGroup):
    waiting_for_message = State()
    waiting_for_admin_reply = State()


class AdminState(StatesGroup):
    menu = State()
    info = State()
    send_message = State()
    user_list = State()
    user_detail = State()


class TokenState(StatesGroup):
    menu = State()
    edit = State()
    add_title = State()
    add_token = State()
    delete = State()
    check = State()


class EditTokenState(StatesGroup):
    menu = State()
    title = State()
    token = State()


class LocationState(StatesGroup):
    get_location = State()


