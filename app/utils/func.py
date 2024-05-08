import random
import re
import io
import string
import asyncio
import os
from datetime import datetime
from thefuzz import fuzz
from contextlib import suppress

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import BufferedInputFile
from aiogram import Bot, Dispatcher

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import select, text

from .config import Settings
from settings import BAN_WORDS, SEND_EXCEPTIONS
from app.database.models import Profile, Users
from app.templates.texts import user as user_text


def subtract_discount(original_amount: int, discount: int) -> int:
    if discount == 0:
        return original_amount

    if discount < 0 or discount > 100:
        raise ValueError("Discount should be between 0 and 100 percent")

    discounted_amount = original_amount * (1 - discount / 100)
    return int(discounted_amount)


async def backup(
    sessionmaker: async_sessionmaker,
    bot: Bot,
    config: Settings
):
    async with sessionmaker() as session:
        async with session.begin():
            session: AsyncSession

            list_id = (await session.scalars(
                select(Users.user_id)
            )).all()

    date_now = datetime.now()
    date_now = date_now.strftime("%d-%m-%Y_%H-%M-%S")

    memory_buffer = io.BytesIO()
    for user_id in list_id:
        memory_buffer.write(str(user_id).encode('utf-8') + b"\n")
    memory_buffer.seek(0)

    input_file = BufferedInputFile(
        file=memory_buffer.getvalue(),
        filename=f"{date_now}.txt"
    )

    await bot.send_document(
        chat_id=config.bot.backup_chat,
        document=input_file
    )


async def lottery(
    sessionmaker: async_sessionmaker,
    bot: Bot
):
    async with sessionmaker() as session:
        async with session.begin():
            session: AsyncSession

            profile_list = (await session.scalars(
                select(Profile)
                .order_by(Profile.time_in_chats.desc())
                .limit(3)
            )).all()

            days = 3

            for profile in profile_list:
                user = await session.scalar(
                    select(Users)
                    .where(Users.user_id == profile.user_id)
                )

                with suppress(*SEND_EXCEPTIONS):
                    await bot.send_message(
                        text=user_text.LOTTERY_WIN.format(days)
                    )

                profile.time_in_chats = 0
                user.add_vip(days)
                days -= 1


def generate_random_code() -> str:
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for _ in range(10))


def clean(text: str) -> str:
    result = re.sub(r'[^a-zA-Zа-яА-Я0-9]', '', text)
    return result


def days_until(target_date: datetime):
    time_difference = target_date - datetime.now()

    if time_difference.total_seconds() < 0:
        return "нет"
    if time_difference.total_seconds() < 3600:
        return f'{int(time_difference.total_seconds() / 60)} минут'
    elif time_difference.days >= 365:
        years = time_difference.days // 365
        return f'{years} год'
    elif time_difference.days < 1:
        return f'{time_difference.seconds // 3600} часов'
    else:
        return f'{time_difference.days} дней'


def kb_wrapper(func):
    annotations = func.__annotations__.get('builder')

    if annotations is None:
        return

    async def async_decorated_function(*args, **kwargs):
        builder = annotations()
        await func(builder, *args, **kwargs)
        return builder.as_markup(resize_keyboard=True)

    def sync_decorated_function(*args, **kwargs):
        builder = annotations()
        func(builder, *args, **kwargs)
        return builder.as_markup(resize_keyboard=True)

    is_async = asyncio.iscoroutinefunction(func)

    return async_decorated_function if is_async else sync_decorated_function


async def state_with(chat_id: int, bot: Bot, dp: Dispatcher) -> FSMContext:
    return FSMContext(
        storage=dp.storage,
        key=StorageKey(
            chat_id=chat_id,
            user_id=chat_id,
            bot_id=bot.id))


# Check response
def check_ban_words(response: str) -> int:
    data = response.lower().split(" ")
    words_count = 0
    for ban_word in BAN_WORDS:
        for word in data:
            if fuzz.ratio(ban_word.lower(), word) > 80:
                words_count += 1
    return words_count


def time_format(seconds: int):
    days, remainder = divmod(int(seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days > 0:
        return f"{days}д {hours}ч и {minutes}м"
    elif hours > 0:
        return f"{hours}ч и {minutes}м"
    elif minutes > 0:
        return f"{minutes}м и {seconds}с"
    else:
        return f"{seconds}с"


async def top_text(session: AsyncSession, user_id: int, bot: Bot) -> str:
    profile = await session.scalar(
        select(Profile)
        .where(Profile.user_id == user_id)
    )

    top_three = (await session.scalars(
        select(Profile)
        .order_by(Profile.time_in_chats.desc())
        .limit(3)
    )).all()

    position = (await session.execute(
        text(f'''
            SELECT pos FROM
            (SELECT user_id, row_number() OVER (ORDER BY time_in_chats DESC) AS pos FROM users.profile) AS sub
            WHERE sub.user_id = {user_id};
        ''')
    )).scalar()

    self_info = await bot.get_chat_member(
        chat_id=user_id,
        user_id=user_id
    )

    top_finish = []

    for top in top_three:
        user_info = await bot.get_chat_member(
            chat_id=top.user_id,
            user_id=top.user_id
        )
        top_finish.append(
            (
                user_info.user.first_name,
                time_format(top.time_in_chats)
            )
        )

    return f'''
Проведи в диалогах больше времени чем остальные и получи приз — подписку <b>💎 PREMIUM</b>

Участие принимают все автоматически, период проведения розыгрыша каждую неделю с понедельника по воскресенье

Подведение итогов и раздача приза каждое воскресенье в 20:00 по МСК.

<i>Призы:</i>
<b>🥇1 место</b> — бесплатная подписка на 3 дня
<b>🥈2 место</b> — бесплатная подписка на 2 дня
<b>🥉3 место</b> — бесплатная подписка на 1 день

<i>Текущие лидеры:</i>
1. <code>{top_finish[0][0]}</code> — в диалогах <code>{top_finish[0][1]}</code>
2. <code>{top_finish[1][0]}</code> — в диалогах <code>{top_finish[1][1]}</code>
3. <code>{top_finish[2][0]}</code> — в диалогах <code>{top_finish[2][1]}</code>

<i>Твоя позиция:</i>
{position}. <code>{self_info.user.first_name}</code> — в диалогах <code>{time_format(profile.time_in_chats)}</code>

<i>❕"Фарм" времени запрещен, а аккаунты с подозрительно низким количеством диалогов и отправленных сообщений будут заблокированы в нашем боте и удалены из ТОПа.</i>
'''
