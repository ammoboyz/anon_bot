from . import (
    user,
    admin
)

from app.utils import Settings
from aiogram import Dispatcher, Router


def setup(dp: Dispatcher, config: Settings):
    """
    Setup all the handlers and routers, bind filters

    :param Dispatcher dp: Dispatcher (root Router)
    """

    user_router = Router()
    admin_router = Router()
    chat_router = Router()

    dp.include_router(admin_router)
    dp.include_router(user_router)
    dp.include_router(chat_router)


    admin.setup(admin_router, config)
    user.setup(user_router, chat_router)
