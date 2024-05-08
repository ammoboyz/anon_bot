from aiogram.fsm.state import State, StatesGroup


class UserState(StatesGroup):
    input_friend_name = State()