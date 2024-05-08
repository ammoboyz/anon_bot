import logging as lg

from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import StateFilter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.utils import AiogramMailling
from app.templates.keyboards import admin as admin_kb
from app.templates.texts import admin as admin_text
from app.database.models import Users, Chats
from app.filters.states.mailling import MaillingState



async def mailling(call: CallbackQuery, state: FSMContext):
    await state.set_state(MaillingState.input)
    await call.message.edit_text(
        text=admin_text.MAILLING,
        reply_markup=admin_kb.inline.admin_back()
    )


async def stop_mailling(call: CallbackQuery, state: FSMContext):
    await state.set_state()

    await call.message.answer(
        text=admin_text.STOP_MAILLING,
        reply_markup=admin_kb.inline.admin_back()
    )


async def mailling_approve(message: Message, state: FSMContext, bot: Bot):
    await state.set_state()

    if message.reply_markup:
        mailling_markup = message.reply_markup.dict()
    else:
        mailling_markup = None

    await state.update_data(
        mailling_msg_id=message.message_id,
        mailling_markup=mailling_markup,
        mailling_caption=message.html_text,
        is_media=True if message.caption else False
    )

    await bot.copy_message(
        chat_id=message.from_user.id,
        from_chat_id=message.from_user.id,
        message_id=message.message_id,
        reply_markup=mailling_markup
    )

    await message.answer(
        text=admin_text.MAILLING_APPROVE,
        reply_markup=admin_kb.inline.mailling_approve()
    )


async def mailling_start(call: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    fsm_data = await state.get_data()

    list_id = (await session.scalars(
        select(Users.user_id)
    )).all()

    list_id += (await session.scalars(
        select(Chats.chat_id)
    )).all()

    mailling_handler = AiogramMailling(
        list_id=list_id,
        bot=bot,
        call=call,
        session=session,
        caption=fsm_data.get('mailling_caption', ""),
        mailling_id=fsm_data.get('mailling_msg_id'),
        mailling_markup=fsm_data.get('mailling_markup'),
        finally_markup=[[InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="admin_menu"
        )]],
        chunk_size=30,
        is_media=fsm_data.get('is_media', True)
    )

    await mailling_handler.mailling_process()


def register(router: Router):
    router.callback_query.register(mailling, F.data == "mailling")
    router.callback_query.register(stop_mailling, F.data == "stop_mailling")

    router.message.register(mailling_approve, StateFilter(MaillingState.input))
    router.callback_query.register(mailling_start, F.data == "mailling_start")