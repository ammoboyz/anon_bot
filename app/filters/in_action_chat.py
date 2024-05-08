from aiogram.filters import Filter
from aiogram.types import Message

from app.templates.texts import user as user_text


class ActionChatFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        if not message:
            return False

        if not message.text:
            return False

        return bool(
            user_text.ACTIONS_DICT.get(message.text.lower(), False)
        )
