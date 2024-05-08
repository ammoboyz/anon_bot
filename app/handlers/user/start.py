import asyncio
from contextlib import suppress

from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import  TelegramRetryAfter

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Users
from app.templates.texts import buttons, user as user_text
from app.templates.keyboards import user as user_kb
from app.utils import func, show_action
from app.templates.texts.commands import START_COMMANDS


async def start(
        message: Message,
        bot: Bot,
        state: FSMContext,
        user: Users,
        session: AsyncSession
):
    with suppress(TelegramRetryAfter):
        await bot.set_my_commands(START_COMMANDS)

    if not user.is_vip:
        await show_action(bot, message.from_user.id, state, session, True)
        await asyncio.sleep(2)

    await message.answer_photo(
        photo="https://telegra.ph/file/4687f4410a726b1204aa8.png",
        caption=user_text.START,
        reply_markup=user_kb.reply.start()
    )


async def call_start(
        call: CallbackQuery,
        bot: Bot,
        state: FSMContext,
        user: Users,
        session: AsyncSession,
        already_hello: bool = False
):
    await call.message.delete()

    with suppress(TelegramRetryAfter):
        await bot.set_my_commands(START_COMMANDS)

    if not user.is_vip and not already_hello:
        await show_action(bot, call.from_user.id, state, session, True)
        await asyncio.sleep(2.5)

    await call.message.answer_photo(
        photo="https://telegra.ph/file/4687f4410a726b1204aa8.png",
        caption=user_text.START,
        reply_markup=user_kb.reply.start()
    )


async def casino(call: CallbackQuery, user: Users):
    await call.message.delete()

    result = await call.message.answer_dice("🎰")

    await asyncio.sleep(2.5)

    days_vip = result.dice.value ** 2
    print(days_vip)
    user.add_vip(days=days_vip)

    await result.reply(
        text=user_text.CASINO.format(
            func.time_format(days_vip * 60 * 60)
        )
    )


async def top(message: Message, bot: Bot, session: AsyncSession):
    finish_text = await func.top_text(session, message.from_user.id, bot)
    await message.answer_photo(
        photo="https://telegra.ph/file/4687f4410a726b1204aa8.png",
        caption=finish_text,
        reply_markup=user_kb.inline.top()
    )


async def add_to_chat(message: Message, bot: Bot):
    bot_info = await bot.get_me()

    await message.answer(
        text=user_text.ADD_TO_CHAT,
        reply_markup=user_kb.inline.start_chat(
            bot_username=bot_info.username,
            text="👉 Добавить бота"
        )
    )


async def clear(message: Message, state: FSMContext):
    await state.clear()

    await message.answer('ok')


def register(router: Router):
    router.message.register(start, CommandStart())
    router.message.register(top, Command("top"))
    router.message.register(add_to_chat, Command("chat"))

    router.callback_query.register(call_start, F.data.in_({"captcha", "check_sub"}))
    router.callback_query.register(casino, F.data == "casino")
    router.message.register(top, F.text == buttons.TOP)
    router.message.register(add_to_chat, F.text == buttons.ADD_TO_CHAT)

    router.message.register(clear, Command('ccclear'))