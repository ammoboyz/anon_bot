from . import (
    start,
    profile,
    dialogue,
    none_register,
    friends,
    premium,
    event,
    settings_search,
    chat
)

from aiogram import Router, F


def setup(router: Router, chat_router: Router):
    """
    Register user handlers.

    :param Dispatcher dp: Dispatcher (root Router), needed for events
    :param Router router: User Router
    """

    router.message.filter(~ F.chat.type.in_({"group", "supergroup"}))
    router.callback_query.filter(~ F.chat.type.in_({"group", "supergroup"}))

    chat_router.message.filter(F.chat.type.in_({"group", "supergroup"}))
    chat_router.callback_query.filter(F.chat.type.in_({"group", "supergroup"}))

    event.register(router)
    none_register.register(router)
    chat.register(chat_router)
    start.register(router)
    profile.register(router)
    friends.register(router)
    premium.register(router)
    settings_search.register(router)
    dialogue.register(router)
