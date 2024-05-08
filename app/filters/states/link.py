from aiogram.fsm.state import State, StatesGroup


class LinkState(StatesGroup):
    link_add = State()
    link_delete = State()