from .session import SessionMiddleware
from .user import UserMiddleware
from .callback import CallbackMiddleware
from .antiflood import AntiFloodMiddleware
from .subscribe import SubscribeMiddleware
from .captcha import CaptchaMiddleware

from aiogram import Dispatcher

from sqlalchemy.ext.asyncio import async_sessionmaker


def setup(dp: Dispatcher, sessionmaker: async_sessionmaker):
    """
    Initialises and binds all the middlewares.

    :param Dispatcher dp: Dispatcher (root Router)
    :param async_sessionmaker sessionmaker: Async Sessionmaker
    """

    dp.message.outer_middleware(AntiFloodMiddleware())
    dp.callback_query.outer_middleware(AntiFloodMiddleware())

    dp.update.outer_middleware(SessionMiddleware(sessionmaker))
    dp.update.outer_middleware(CaptchaMiddleware())
    dp.update.outer_middleware(UserMiddleware())
    dp.update.outer_middleware(SubscribeMiddleware())

    dp.callback_query.outer_middleware(CallbackMiddleware())
