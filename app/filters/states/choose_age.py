from aiogram.fsm.state import State, StatesGroup


class ClientState(StatesGroup):
    input_age = State()
    input_sex = State()

    input_sex_none_reg = State()
    input_age_none_reg = State()