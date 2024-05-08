from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from app.templates.texts import buttons

from app.utils.func import kb_wrapper


@kb_wrapper
def start(builder: ReplyKeyboardBuilder) -> ReplyKeyboardMarkup:
    builder.button(text=buttons.FIND_CHAT)
    builder.button(text=buttons.PREMIUM)
    builder.button(text=buttons.CHANGE_SEARCH)
    builder.button(text=buttons.PROFILE)
    builder.button(text=buttons.TOP)
    builder.button(text=buttons.ADD_TO_CHAT)
    builder.button(text=buttons.FRIENDS)

    builder.adjust(1, 2, 2, 2)


@kb_wrapper
def dialogue(builder: ReplyKeyboardBuilder) -> ReplyKeyboardMarkup:
    builder.button(text=buttons.ADD_FRIEND)
    builder.button(text=buttons.STOP_DIALOG)
    builder.button(text=buttons.TARGET_MAN)
    builder.button(text=buttons.TARGET_WOMAN)

    builder.adjust(2)
