from typing import Any, Awaitable, Callable, Dict
from contextlib import suppress

from aiogram import BaseMiddleware
from aiogram.types import Update

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncSession
)


class SessionMiddleware(BaseMiddleware):
    """
    Middleware for adding session.
    """

    def __init__(self, sessionmaker: async_sessionmaker):
        self.sessionmaker = sessionmaker

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        async with self.sessionmaker() as session:
            async with session.begin():
                session: AsyncSession
                data["session"] = session
                try:
                    await handler(event, data)
                finally:
                    await session.commit()
                    await session.close()
