import json
import arrow
from datetime import datetime

from aiogram.filters import Command
from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery

from sqlalchemy import delete, or_, select
from sqlalchemy.future import select as select_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Profile, Users
from app.templates.texts import buttons, user as user_text
from app.templates.keyboards import user as user_kb


async def friends_menu(
        update: Message | CallbackQuery,
        session: AsyncSession,
        bot: Bot,
        router: Router
    ):
    profile = await session.scalar(
        select(Profile)
        .where(Profile.user_id == update.from_user.id)
    )

    friends_id_list: list = json.loads(profile.friends)
    friends_dict = {}

    for friend_id in friends_id_list:
        try:
            user_instance = await bot.get_chat_member(
                chat_id=int(friend_id),
                user_id=int(friend_id)
            )
            username = user_instance.user.first_name
        except Exception as e:
            username = "Дружок"

        friends_dict[friend_id] = username

    if isinstance(update, Message):
        await update.answer_photo(
            photo="https://telegra.ph/file/4687f4410a726b1204aa8.png",
            caption=user_text.NONE_FRIENDS if not friends_dict else "",
            reply_markup=user_kb.inline.friends_menu(friends_dict, router)
        )

    elif isinstance(update, CallbackQuery):
        await update.message.edit_caption(
            caption=user_text.NONE_FRIENDS if not friends_dict else "",
            reply_markup=user_kb.inline.friends_menu(friends_dict, router)
        )


async def friend(call: CallbackQuery, bot: Bot, session: AsyncSession):
    friend_id = int(call.data.split(":")[1])

    profile_friend = await session.scalar(
        select(Profile)
        .where(Profile.user_id == friend_id)
    )

    friend_user = await session.scalar(
        select(Users)
        .where(Users.user_id == friend_id)
    )

    friend_instance = await bot.get_chat_member(
        chat_id=friend_id,
        user_id=friend_id
    )

    gender_str = (
        "М 🧑🏻" if friend_user.is_man
        else "Д 👩🏼"
    )

    dt = arrow.utcnow().shift(
        seconds=-(
            datetime.now() - friend_user.last_online
        ).total_seconds()
    )
    humanize_time = dt.humanize(locale='ru')

    await call.message.edit_caption(
        caption=user_text.FRIEND_PROFILE.format(
            full_name=friend_instance.user.full_name,
            gender=gender_str,
            humanize_time=humanize_time,
            fire=profile_friend.fire,
            satan=profile_friend.satan,
            clown=profile_friend.clown,
            shit=profile_friend.shit,
            premium="есть" if friend_user.is_vip else "отсутствует"
        ),
        reply_markup=user_kb.inline.friend(friend_id=friend_id)
    )


async def friend_delete(call: CallbackQuery, bot: Bot, session: AsyncSession):
    friend_id = int(call.data.split(":")[1])

    for user_id in [call.from_user.id, friend_id]:
        second_id = friend_id if user_id == call.from_user.id else call.from_user.id

        profile = await session.scalar(
            select(Profile)
            .where(Profile.user_id == user_id)
        )

        friends_list: list = json.loads(profile.friends)

        if second_id in friends_list:
            friends_list.remove(second_id)

        profile.friends = json.dumps(friends_list)

    friend_instance = await bot.get_chat_member(
        chat_id=friend_id,
        user_id=friend_id
    )

    await call.message.edit_caption(
        caption=user_text.FRIEND_DELETE.format(
            friend_instance.user.first_name
        ),
        reply_markup=user_kb.inline.back_to_friends_menu()
    )


def register(router: Router):
    router.message.register(friends_menu, F.text == buttons.FRIENDS)
    router.message.register(friends_menu, Command("bro"))

    router.callback_query.register(friends_menu, F.data == "friends_menu")
    router.callback_query.register(friend, F.data.startswith("friend:"))
    router.callback_query.register(friend_delete, F.data.startswith("friend_delete"))
