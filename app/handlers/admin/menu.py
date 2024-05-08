import datetime
import sys, os

from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, BufferedInputFile, InputMediaPhoto, FSInputFile
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.models import Users, Captcha
from app.utils import admin_func
from app.templates.keyboards import admin as admin_kb
from app.templates.texts import admin as admin_text


async def admin_menu(message: Message):
    await message.answer(
        text=admin_text.ADMIN_MENU,
        reply_markup=admin_kb.inline.admin_menu()
    )


async def call_admin_menu(call: CallbackQuery, state: FSMContext):
    await state.set_state()

    await call.message.delete()
    await call.message.answer(
        text=admin_text.ADMIN_MENU,
        reply_markup=admin_kb.inline.admin_menu()
    )


async def stat(call: CallbackQuery, session: AsyncSession, bot: Bot):
    data = call.data.split("_")
    interval = int(data[1])
    bot_info = await bot.me()

    image_stats = await admin_func.StatisticsPlotter(
        interval=interval,
        session=session
    ).plot_statistics()

    string_stats = await admin_func.StatisticString(
        session=session,
        bot_username=bot_info.username
    ).all_statistics()

    if call.message.photo:
        await call.message.edit_media(
                media=InputMediaPhoto(
                    media=BufferedInputFile(
                        image_stats.getvalue(),
                        filename="stats.png"
                    ),
                caption=string_stats,
                parse_mode="HTML"
            ),
            reply_markup=admin_kb.inline.stats(interval))
    else:
        await call.message.delete()
        await call.message.answer_photo(
            photo=BufferedInputFile(
                image_stats.getvalue(),
                filename="stats.png"
            ),
            caption=string_stats,
            reply_markup=admin_kb.inline.stats(interval)
        )


async def download_db(call: CallbackQuery, session: AsyncSession):
    users_list = (await session.scalars(
        select(Users.user_id)
    )).all()

    with open("user_ids.txt", "w") as file:
        for user in users_list:
            file.write(str(user) + "\n")
    document = FSInputFile("user_ids.txt")

    await call.message.delete()
    await call.message.answer_document(
        document=document,
        caption=f"<b>📃 Чтобы вернуться в админ панель /admin</b>"
    )


async def restart(call: CallbackQuery):
    await call.message.edit_text(
        text='<b>🔁 Перезапускаю...</b>\n\n'
        '<i>Ожидайте 5 секунд!</i>',
        reply_markup=admin_kb.inline.go_back()
    )
    python = sys.executable
    os.execl(python, python, *sys.argv)


def register(router: Router):
    router.message.register(admin_menu, Command("admin"))
    router.callback_query.register(call_admin_menu, F.data == "admin_menu")
    router.callback_query.register(stat, F.data.startswith("stat_"))
    router.callback_query.register(restart, F.data == "restart")
    router.callback_query.register(download_db, F.data == "download_db")