from app.utils.config import Settings
from app.database.models import Users

from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery


class IsAdmin(Filter):
    """
    Check if user is an admin
    """

    async def __call__(self, update: Message | CallbackQuery, config: Settings) -> bool:
        return update.from_user.id in config.bot.admins
