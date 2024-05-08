from aiogram.fsm.state import State, StatesGroup


class MaillingState(StatesGroup):
    input = State()