from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery

from app.database.models import Users


class IsVipFilter(Filter):
    """
    Check if user vip
    """

    async def __call__(self, update: Message | CallbackQuery, user: Users) -> bool:
        a = user.is_vip
        print(a)
        return a