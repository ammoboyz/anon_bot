import random
from datetime import datetime, timedelta
from typing import Union
from contextlib import suppress

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ChatMemberUpdated, BotCommand
from aiogram.fsm.context import FSMContext
from aiogram.filters.chat_member_updated import (
    ChatMemberUpdatedFilter, JOIN_TRANSITION, LEAVE_TRANSITION
)

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.database.models import Users, Chats
from app.filters import ActionChatFilter
from app.templates.texts import user as user_text
from app.templates.keyboards import user as user_kb
from app.utils import show_action


async def info_chat(message: Message):
    await message.reply(
        text=user_text.INFO_CHATS,
        disable_web_page_preview=True
    )


async def game_chat(message: Message, user: Users):
    if (user.last_game + timedelta(days=1)) > datetime.now():
        return await message.reply(
            text=user_text.GAME_ERROR.format(
                user_id=message.from_user.id,
                first_name=message.from_user.first_name
            ),
            disable_web_page_preview=True
        )

    await message.reply(
        text=user_text.GAME_START.format(
            user_id=message.from_user.id,
            first_name=message.from_user.first_name
        ),
        disable_web_page_preview=True,
        reply_markup=user_kb.inline.game(
            user_id=message.from_user.id
        )
    )


async def game_result(call: CallbackQuery, bot: Bot, state: FSMContext, user: Users, session: AsyncSession):
    user_id, result = call.data.split(":")[1:]
    user_id = int(user_id)
    result = int(result)
    print(user_id, result)

    if user_id != call.from_user.id:
        return

    bot_info = await bot.get_me()
    user.last_game = datetime.now()

    if not result:
        await call.message.edit_text(
            text=user_text.GAME_OVER.format(
            user_id=call.from_user.id,
            first_name=call.from_user.first_name
            ),
            disable_web_page_preview=True
        )

    elif result:
        user.add_vip(hours=2)

        await call.message.edit_text(
            text=user_text.GAME_WIN.format(
                first_name=call.from_user.first_name,
                bot_username=bot_info.username
            ),
            disable_web_page_preview=True
        )

    await show_action(bot, call.message.chat.id, state, session)


async def start_chat(event: Union[Message, ChatMemberUpdated], bot: Bot, session: AsyncSession):
    await bot.set_my_commands(
        commands=[
            BotCommand(
                command="/start",
                description="▶️ Открыть меню"
            ),
            BotCommand(
                command="/game",
                description="🥚Игра в яичко"
            ),
            BotCommand(
                command="/info",
                description="🔖 Инструкция"
            )
        ]
    )

    new_chat = Chats(
        chat_id=event.chat.id
    )

    with suppress(IntegrityError):
        await session.merge(new_chat)

    bot_info = await bot.get_me()

    await bot.send_photo(
        chat_id=event.chat.id,
        photo="https://telegra.ph/file/4687f4410a726b1204aa8.png",
        caption=user_text.START_CHAT.format(
            first_name=event.from_user.first_name
        ),
        reply_markup=user_kb.inline.start_chat(bot_username=bot_info.username)
    )


async def ball_chat(message: Message, bot: Bot, state: FSMContext, session: AsyncSession):
    result = random.randint(0, 1)

    await message.reply(f"Шар уверен, что {'да' if result else 'нет'}")

    await show_action(bot, message.chat.id, state, session)


async def actions_chat(message: Message):
    await message.reply(
        text=f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a> {user_text.ACTIONS_DICT.get(message.text)} <a href='tg://user?id={message.reply_to_message.from_user.id}'>{message.reply_to_message.from_user.first_name}</a>"
    )


async def delete_chat(event: ChatMemberUpdated, session: AsyncSession):
    await session.execute(
        delete(Chats)
        .where(Chats.chat_id == event.chat.id)
    )


def register(router: Router):
    router.my_chat_member.register(start_chat, ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
    router.my_chat_member.register(delete_chat, ChatMemberUpdatedFilter(member_status_changed=LEAVE_TRANSITION))
    router.message.register(start_chat, Command("start"))
    router.message.register(info_chat, Command("info"))
    router.message.register(game_chat, Command("game"))
    router.message.register(ball_chat, F.text.lower().startswith("шар"))
    router.message.register(actions_chat, ActionChatFilter())

    router.callback_query.register(game_result, F.data.startswith("game:"))
