from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.models import Queue


class InQueueFilter(Filter):
    """
    Check if user in queue
    """

    async def __call__(self, update: Message | CallbackQuery, session: AsyncSession) -> bool:
        match = await session.scalar(
            select(Queue)
            .where(Queue.user_id == update.from_user.id)
        )
        return match is not None
