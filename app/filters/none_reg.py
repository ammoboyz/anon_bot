from app.database.models import Users

from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery


class NoneRegisterFilter(Filter):
    """
    Check if user none register
    """

    async def __call__(self, update: Message | CallbackQuery, user: Users) -> bool:
        return (user.is_man is None) or (user.age is None)
