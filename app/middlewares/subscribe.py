from contextlib import suppress
from typing import Any, Awaitable, Callable, Dict, Optional
import logging as lg
import time

from aiogram import BaseMiddleware, Bot, exceptions
from aiogram.types import Update, User, InlineKeyboardMarkup, Chat
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from settings import SEND_EXCEPTIONS
from app.templates.texts import user as user_text
from app.database.models import Sponsors, Users
from app.utils import Settings, admin_func


class SubscribeMiddleware(BaseMiddleware):
    """
    Middleware for filter in subscribe sponsors.
    """

    @staticmethod
    def sponsors_kb(sponsors_list: list[Sponsors]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        adjust_list = []
        i = 0

        for sponsor in sponsors_list:
            i += 1
            first_name = f"Канал #{i}"#sponsor.first_name

            if i % 2 == 0:
                adjust_list.append(2)

            builder.button(
                text=first_name,
                url=sponsor.url
            )

        builder.button(
            text="💎 Убрать рекламу",
            callback_data="premium_list"
        )

        builder.button(
            text="Готово",
            callback_data="check_sub"
        )

        adjust_list += [1, 1]

        builder.adjust(*adjust_list)
        return builder.as_markup()


    @staticmethod
    async def check_sub(sponsors_list: list[Sponsors], bot: Bot, user_id: int, config: Settings) -> tuple[bool, list]:
        not_susbscribed_list = []
        subscribed_to_all = True

        for sponsor in sponsors_list:
            if sponsor.is_show:
                continue

            subscribed_to_sponsor = True

            if sponsor.is_bot:
                try:
                    bot_instance = Bot(sponsor.token)
                    await bot_instance.send_chat_action(
                        chat_id=user_id,
                        action="typing"
                    )
                except (
                    exceptions.TelegramForbiddenError,
                    exceptions.TelegramBadRequest
                ):
                    subscribed_to_sponsor = False
                    subscribed_to_all = False
                    not_susbscribed_list.append(sponsor)
                except Exception as e:
                    lg.error(f'middleware sub -> {e}')
                finally:
                    await bot_instance.session.close()
            else:
                try:
                    x = await bot.get_chat_member(sponsor.id, user_id)
                    if x.status not in ["member", "creator", "administrator"]:
                        subscribed_to_sponsor = False
                        subscribed_to_all = False
                        not_susbscribed_list.append(sponsor)
                except (
                    exceptions.TelegramForbiddenError,
                    exceptions.TelegramBadRequest
                ):
                    await admin_func.report(
                        text=f"⚠️ <b>Добавьте бота как админа в канал <a href='{sponsor.url}'>{sponsor.first_name}</a></b>",
                        list_id=config.bot.admins,
                        bot=bot
                    )
                except Exception as e:
                    lg.error(e)

        return subscribed_to_all, not_susbscribed_list


    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:

        bot: Bot = data['bot']
        config: Settings = data['config']
        event_user: Optional[User] = data.get("event_from_user")
        user: Optional[Users] = data.get("user")
        session: AsyncSession = data['session']
        state: FSMContext = data['state']
        chat: Optional[Chat] = data.get('event_chat')

        state_data = await state.get_data()
        time_to_check: bool = state_data.get('last_check', 0) < (time.time() - 60)

        if chat.type in ["supergroup", "group"]:
            return await handler(event, data)

        if event.my_chat_member:
            return await handler(event, data)

        if event.callback_query:
            if event.callback_query.data.startswith(("premium", "choise_sex_none_reg", "add_age")):
                return await handler(event, data)

        if (not time_to_check) or (chat.type != 'private') or (getattr(user, 'is_vip', False)) or (event_user.id in config.bot.admins):
            user.passed_op = True
            return await handler(event, data)

        sponsors = (await session.scalars(
            select(Sponsors)
        )).all()

        subscribed_to_all, not_susbscribed_list = await self.check_sub(
            sponsors_list=sponsors,
            bot=bot,
            user_id=event_user.id,
            config=config
        )

        if subscribed_to_all:
            await state.update_data(
                last_check=time.time()
            )

            if not user.passed_op:
                for sponsor in sponsors:
                    sponsor.count += 1

            user.passed_op = True

            return await handler(event, data)

        user.passed_op = False

        if event.callback_query:
            if event.callback_query.data == "check_sub":
                with suppress(*SEND_EXCEPTIONS):
                    return await bot.answer_callback_query(
                        callback_query_id=event.callback_query.id,
                        show_alert=True,
                        text=user_text.NOT_ALL_SUBSCRIPTION
                    )

        with suppress(*SEND_EXCEPTIONS):
            return await bot.send_message(
                chat_id=event_user.id,
                text=user_text.SUBSCRIPTION_SPONSORS,
                reply_markup=self.sponsors_kb(not_susbscribed_list)
            )
