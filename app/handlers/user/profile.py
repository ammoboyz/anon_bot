import arrow
import json
from datetime import datetime, timedelta

from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.utils import InterestsCallbackFactory, func
from app.database.models import Users, Profile
from app.templates.texts import buttons, user as user_text
from app.templates.keyboards import user as user_kb


async def profile(update: Message | CallbackQuery):
    kwargs_message = {
        "photo": "https://telegra.ph/file/4687f4410a726b1204aa8.png",
        "reply_markup": user_kb.inline.profile()
    }

    if isinstance(update, Message):
        await update.answer_photo(**kwargs_message)

    elif isinstance(update, CallbackQuery):
        await update.message.edit_caption(**kwargs_message)


async def profile_user(update: Message | CallbackQuery, session: AsyncSession, bot: Bot, user: Users):
    profile = await session.scalar(
        select(Profile)
        .where(Profile.user_id == update.from_user.id)
    )

    bot_info = await bot.get_me()

    interests: list = json.loads(profile.interests.replace("'", '"'))
    interests_str = (
        ', '.join(interests)
        if interests else 'не выбраны'
    )

    premium = "отсутствует"

    if user.is_vip:
        if user.vip_time > (datetime.now() + timedelta(days=365)):
            premium = "бесконечный"
        else:
            dt = arrow.utcnow().shift(
                seconds=(
                    user.vip_time - datetime.now()
                ).total_seconds()
            )
            premium = "истечёт " + dt.humanize(locale='ru')

    text_kwargs = {
        'user_id': update.from_user.id,
        'gender': "М 🧑🏻" if user.is_man else "Д 👩🏼",
        'age': user.age,
        'interests': interests_str,
        'fire': profile.fire,
        'satan': profile.satan,
        'clown': profile.clown,
        'shit': profile.shit,
        'bot_username': bot_info.username,
        'premium': premium
    }

    msg_kwargs = {
        "caption": user_text.PROFILE.format(**text_kwargs),
        "reply_markup": user_kb.inline.profile_user()
    }

    if isinstance(update, Message):
        await update.edit_caption(**msg_kwargs)

    elif isinstance(update, CallbackQuery):
        await update.message.edit_caption(**msg_kwargs)


async def change_age_one(call: CallbackQuery):
    await call.message.edit_caption(
        caption=user_text.CHANGE_AGE,
        reply_markup=user_kb.inline.change_age(action_type="profile_age")
    )


async def change_age_two(call: CallbackQuery, session: AsyncSession, bot: Bot, user: Users):
    age = int(call.data.split(":")[1])

    user.age = int(age)
    return await profile_user(call, session, bot, user)


async def change_gender_one(call: CallbackQuery):
    await call.message.edit_caption(
        caption=user_text.CHANGE_SEX,
        reply_markup=user_kb.inline.change_gender("profile_gender")
    )


async def change_gender_two(
        call: CallbackQuery,
        session: AsyncSession,
        bot: Bot,
        user: Users
):
    sex = call.data.split(":")[1]

    user.is_man = True if sex == "man" else False
    await profile_user(call, session, bot, user)


async def change_interests(
        call: CallbackQuery,
        session: AsyncSession,
        bot: Bot,
        user: Users,
        callback_data: InterestsCallbackFactory = None
):
    profile = await session.scalar(
        select(Profile)
        .where(Profile.user_id == call.from_user.id)
    )

    if not callback_data:
        profile.interests = '[]'

        return await call.message.edit_caption(
            caption=user_text.CHANGE_INTERESTS,
            reply_markup=user_kb.inline.change_interests(
                callback_data=callback_data,
                already_interests=str(profile.interests)
            )
        )

    if callback_data.is_active:
        return

    interests_list: list = json.loads(profile.interests)
    interests_list.append(callback_data.interest)
    interests_list = list(set(interests_list))
    profile.interests = str(interests_list).replace("'", '"')

    if len(interests_list) >= 3:
        return await profile_user(call, session, bot, user)

    await call.message.edit_reply_markup(
        reply_markup=user_kb.inline.change_interests(
            callback_data=callback_data,
            already_interests=interests_list
        )
    )


async def nullable_rate(call: CallbackQuery):
    await call.message.edit_caption(
        caption=user_text.NULLABLE_RATE,
        reply_markup=user_kb.inline.nullable_rate()
    )


async def profile_stats(call: CallbackQuery, session: AsyncSession, user: Users):
    profile = await session.scalar(
        select(Profile)
        .where(Profile.user_id == call.from_user.id)
    )

    await call.message.edit_caption(
        caption=user_text.PROFILE_STATS.format(
            reg_date=user.reg_date,
            dialogue_count=profile.dialogue_count,
            message_count=profile.message_count,
            time_in_chats=func.time_format(profile.time_in_chats),
            swear_count=profile.swear_count,
            anon_count=profile.anon_count,
            ref_count=user.referal_count
        ),
        reply_markup=user_kb.inline.profile_stats()
    )


def register(router: Router):
    router.message.register(profile, F.text == buttons.PROFILE)
    router.message.register(profile, Command("profile"))

    router.callback_query.register(profile, F.data == "profile")

    router.callback_query.register(profile_user, F.data == "profile_user")
    router.callback_query.register(profile_stats, F.data == "profile_stats")

    router.callback_query.register(change_age_one, F.data == "profile_change:age")
    router.callback_query.register(change_age_two, F.data.startswith("profile_age:"))

    router.callback_query.register(change_gender_one, F.data == "profile_change:gender")
    router.callback_query.register(change_gender_two, F.data.startswith("profile_gender:"))

    router.callback_query.register(change_interests, F.data == "profile_change:interests")
    router.callback_query.register(change_interests, InterestsCallbackFactory.filter(F.action == "change_interests"))

    router.callback_query.register(nullable_rate, F.data == "profile_change:nullable_rate")
