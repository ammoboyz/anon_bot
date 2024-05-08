from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message, BufferedInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.filters.states.link import LinkState
from app.database.models import Advertising, Users
from app.utils import func, admin_func
from app.templates.keyboards import admin as admin_kb
from app.utils.config import Settings


async def link_add_one(call: CallbackQuery, state: FSMContext):
    await state.set_state(LinkState.link_add)
    await call.message.edit_text(
        text="<b>⛓ Отправь название ссылки.</b>",
        reply_markup=admin_kb.inline.go_back("link_menu"))


async def link_add_two(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    bot_info = await bot.me()

    try:
        link_token = func.generate_random_code()
        ads_link = Advertising(
            token=link_token,
            name=message.text
        )
        await session.merge(ads_link)

        await message.answer(
            text=f"<b>✅ Реферальная ссылка <code>{message.text}</code> добавлена:\n\n</b>"
                 f"<code>https://t.me/{bot_info.username}?start=ads{link_token}</code>",
            reply_markup=admin_kb.inline.go_back("link_menu"))

        await state.set_state()
    except Exception as e:
        await message.answer(
            text=f"Бот не может выполнить данный скрипт по причине: <code>{e}</code>",
            reply_markup=admin_kb.inline.go_back("link_menu"))


async def sure_delete_link(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    token = call.data.split("_")[2]

    link_name = await session.scalar(
        select(Advertising.name)
        .where(Advertising.token == token)
    )

    await call.message.delete()
    await call.message.answer(
        text=f"<b>⛓ Ты уверен что хочешь удалить рекламную ссылку <code>{link_name}</code>?</b>",
        reply_markup=admin_kb.inline.sure_delete_link(token)
    )


async def delete_link(call: CallbackQuery, session: AsyncSession):
    token = call.data.split("_")[1]

    try:
        link_name = await session.scalar(
            select(Advertising.name)
            .where(Advertising.token == token)
        )

        await session.execute(
            delete(Advertising)
            .where(Advertising.token == token)
        )

        await call.message.edit_text(
            text=f"<b>✅ Реферальная ссылка <code>{link_name}</code> удалена!</b>",
            reply_markup=admin_kb.inline.go_back("link_menu")
        )
    except Exception as e:
        await call.message.answer(
            text=f"Бот не может выполнить данный скрипт по причине: <code>{e}</code>",
            reply_markup=admin_kb.inline.go_back("link_menu")
        )


async def link_menu(call: CallbackQuery, state: FSMContext, session: AsyncSession, router: Router):
    await state.set_state()

    ads_list = (await session.scalars(
        select(Advertising)
        .order_by(Advertising.date)
    )).all()

    await call.message.delete()
    await call.message.answer(
        text="<b>⛓ Реферальное меню:</b>",
        reply_markup=admin_kb.inline.link_menu(ads_list, router)
    )


async def link_stats(call: CallbackQuery, session: AsyncSession, bot: Bot):
    data = call.data.split("_")
    token = data[1]
    interval = int(data[2])
    bot_info = await bot.me()

    stats_image = await admin_func.StatisticsPlotter(
        interval=interval,
        session=session,
        ads_token=token
    ).plot_statistics()

    string_stats = await admin_func.StatisticString(
        session=session,
        bot_username=bot_info.username,
        ads_token=token
    ).ads_statistics()

    if call.message.photo:
        await call.message.edit_media(
            media=InputMediaPhoto(
                media=BufferedInputFile(
                    stats_image.getvalue(),
                    filename="stats.png"
                ),
                caption=string_stats,
                parse_mode="HTML"
            ),
            reply_markup=admin_kb.inline.link_manage(token, interval)
        )
    else:
        await call.message.delete()
        await call.message.answer_photo(
            photo=BufferedInputFile(
                stats_image.getvalue(),
                filename="stats.png"
            ),
            caption=string_stats,
            reply_markup=admin_kb.inline.link_manage(token, interval)
        )


def register(router: Router):
    router.callback_query.register(link_menu, F.data == "link_menu")
    router.callback_query.register(link_stats, F.data.startswith("linkstat"))

    router.callback_query.register(link_add_one, F.data == "link_add")
    router.message.register(link_add_two, F.text, StateFilter(LinkState.link_add))

    router.callback_query.register(sure_delete_link, F.data.startswith("sure_delete_"))
    router.callback_query.register(delete_link, F.data.startswith("delete_"))
