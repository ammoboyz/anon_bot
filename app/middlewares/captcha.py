import asyncio
import logging as lg

from typing import Any, Awaitable, Callable, Dict, Optional
from contextlib import suppress

from aiogram import BaseMiddleware, types, Bot
from aiogram.types import Update, Chat
from aiogram.fsm.context import FSMContext

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.utils import show_action
from app.database.models import Captcha
from app.templates.texts import user as user_text
from app.templates.keyboards import user as user_kb
from settings import SEND_EXCEPTIONS


class CaptchaMiddleware(BaseMiddleware):
    """
    Middleware for captcha.
    """

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:

        event_user: Optional[types.User] = data.get("event_from_user")
        session: AsyncSession = data['session']
        bot: Bot = data['bot']
        state: FSMContext = data['state']
        chat: Optional[Chat] = data.get('event_chat')

        if chat.type in ["supergroup", "group"]:
            return await handler(event, data)

        user_captcha = await session.scalar(
            select(Captcha)
            .where(Captcha.user_id == event_user.id)
        )

        where_from = ""
        if event.message:
            if event.message.text:
                if event.message.text.startswith("/start") and len(event.message.text.split()) == 2:
                    where_from = event.message.text.split()[1]

        if user_captcha is None and not event.inline_query:
            new_user_captcha = Captcha(
                user_id=event_user.id,
                where_from=where_from[3:]
            )

            await session.merge(new_user_captcha)

            user_captcha = await session.scalar(
                select(Captcha)
                .where(Captcha.user_id == event_user.id)
            )

        if user_captcha.done:
            return await handler(event, data)

        if event.message:
            if event.message.text and event.message.text.startswith("/start"):
                fsm_data = await state.get_data()

                if not fsm_data.get('start_msg'):
                    await state.update_data(
                        start_msg=event.message.text
                    )

            await show_action(bot, event_user.id, state, session, True)
            await asyncio.sleep(2)

            with suppress(*SEND_EXCEPTIONS):
                return await bot.send_photo(
                    chat_id=event_user.id,
                    photo="https://telegra.ph/file/4687f4410a726b1204aa8.png",
                    caption=user_text.CAPTCHA_CHOOSE_SEX,
                    reply_markup=user_kb.inline.captcha()
                )

        if event.callback_query:
            user_captcha.done = True

        return await handler(event, data)
