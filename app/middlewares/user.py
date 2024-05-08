from typing import Any, Awaitable, Callable, Dict, Optional
from datetime import datetime
from contextlib import suppress

from aiogram import BaseMiddleware, types, Bot
from aiogram.fsm.context import FSMContext

from sqlalchemy import update
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.templates.texts import user as user_text
from app.database.models import Users, Advertising, Profile, Captcha
from settings import SEND_EXCEPTIONS


class UserMiddleware(BaseMiddleware):
    """
    Middleware for registering user.
    """

    @staticmethod
    async def captcha_edit(user_id: int, ads_token: str, session: AsyncSession) -> None:
        await session.execute(
            update(Captcha)
            .where(Captcha.user_id == user_id)
            .values(where_from = ads_token[3:])
        )


    @staticmethod
    async def plus_ref(link: str, bot: Bot, session: AsyncSession):
        referral = await session.scalar(
            select(Users)
            .where(Users.user_id == int(link))
        )

        if not referral:
            return

        referral.referal_count += 1
        referral.add_vip(hours=2)

        with suppress(*SEND_EXCEPTIONS):
            await bot.send_message(
                chat_id=referral.user_id,
                text=user_text.JOIN_FRIEND.format(2)
            )


    @staticmethod
    async def plus_ads(link: str, session: AsyncSession):
        ads_link = await session.scalar(
            select(Advertising)
            .where(Advertising.token == link)
        )

        if not ads_link:
            return

        ads_link.count += 1


    async def reg_user(
            self,
            event: types.Update,
            session: AsyncSession,
            event_user: types.User,
            state: FSMContext,
            bot: Bot,
            chat: types.Chat
    ) -> tuple[Users, Profile]:
        ref_link = ""
        ref_list = []

        if event.callback_query:
            fsm_data = await state.get_data()
            start_msg: str = fsm_data.get('start_msg', '/start')
            ref_list = start_msg.split()

        elif event.message:
            if event.message.text:
                if event.message.text.startswith('/start'):
                    ref_list = event.message.text.split()

        if len(ref_list) > 1:
            ref_link: str = ref_list[1]

        await self.captcha_edit(event_user.id, ref_link, session)

        if ref_link.startswith("ads"):
            await self.plus_ads(
                link=ref_link[3:],
                session=session
            )

        elif ref_link.startswith("r"):
            await self.plus_ref(
                link=ref_link[1:],
                bot=bot,
                session=session
            )

        if chat.type in ["supergroup", "group"]:
            from_group = True
        else:
            from_group = False

        user = Users(
            user_id=event_user.id,
            where_from=(
                ref_link[3:] if ref_link.startswith("ads")
                else ref_link[1:]
            ),
            from_group=from_group
        )

        profile = Profile(
            user_id=event_user.id
        )

        with suppress(IntegrityError):
            await session.merge(user)

        with suppress(IntegrityError):
            await session.merge(profile)

        return await self.get_records(session, event_user.id)


    @staticmethod
    async def get_records(session: AsyncSession, user_id: int):
        user = await session.scalar(
            select(Users)
            .where(Users.user_id == user_id)
        )

        profile = await session.scalar(
            select(Profile)
            .where(Profile.user_id == user_id)
        )

        return user, profile


    async def __call__(
        self,
        handler: Callable[[types.Update, Dict[str, Any]], Awaitable[Any]],
        event: types.Update,
        data: Dict[str, Any],
    ) -> Any:

        event_user: Optional[types.User] = data.get("event_from_user")
        session: AsyncSession = data['session']
        bot: Bot = data['bot']
        state: FSMContext = data['state']
        chat: Optional[types.Chat] = data.get('event_chat')

        user, profile = await self.get_records(session, event_user.id)

        if chat.type in ["supergroup", "group"]:
            if event.message:
                if event.message.text:
                    if not event.message.text.lower().startswith(("/start", "/game", "/info", "шар", *user_text.ACTIONS_DICT)):
                        return
                else:
                    return

        if user is None and not event.inline_query:
            user, profile = await self.reg_user(event, session, event_user, state, bot, chat)

        user.last_online = datetime.now()

        if user.banned:
            return

        if user.dead:
            user.dead = False

        data["user"] = user
        data["profile"] = profile

        return await handler(event, data)
