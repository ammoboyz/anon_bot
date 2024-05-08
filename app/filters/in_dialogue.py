from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Dialogues


class InDialogueFilter(Filter):
    """
    Check if user in dialogue
    """

    async def __call__(self, update: Message | CallbackQuery, session: AsyncSession) -> bool:
        dialogue = await Dialogues.get_dialogue(
            user_id=update.from_user.id,
            session=session
        )

        return dialogue is not None
