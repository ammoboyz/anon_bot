import json

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.filters import IsVipFilter
from app.database.models import Users, Profile
from app.templates.texts import buttons, user as user_text
from app.templates.keyboards import user as user_kb


async def change_search(update: Message | CallbackQuery, user: Users, session: AsyncSession):
    profile = await session.scalar(
        select(Profile)
        .where(Profile.user_id == update.from_user.id)
    )

    options_gender = {
        True: "М 🧑🏻",
        False: "Д 👩🏼",
        None: "Любой"
    }

    options_age = {
        (8, 9, 10): "8-10",
        (11, 12, 13): "11-13",
        (14, 15, 16): "14-16",
        (17, 18, 19): "17-19",
        (20, 21, 22): "20-22",
        (22, 23, 24): "22+",
        (): "любой"
    }

    msg_kwargs = {
        "photo": "https://telegra.ph/file/4687f4410a726b1204aa8.png",
        "caption": user_text.CHANGE_SEARCH.format(
            gender=options_gender.get(profile.target_man),
            age=options_age.get(tuple(json.loads(profile.target_age))),
            room=profile.target_room or "общая"
        ),
        "reply_markup": user_kb.inline.change_search()
    }

    if isinstance(update, Message):
        await update.answer_photo(**msg_kwargs)

    elif isinstance(update, CallbackQuery):
        await update.message.edit_caption(**msg_kwargs)


async def change_search_gender(call: CallbackQuery, user: Users, session: AsyncSession):
    call_data = call.data.split(":")

    profile = await session.scalar(
        select(Profile)
        .where(Profile.user_id == call.from_user.id)
    )

    options_gender = {"man": True, "woman": False, "any": None}

    if len(call_data) == 3:
        profile.target_man = options_gender.get(call_data[2])

    await call.message.edit_caption(
        caption=user_text.CHANGE_SEARCH_CHOOSE,
        reply_markup=user_kb.inline.change_search_gender(
            target_man=profile.target_man
        )
    )


async def change_search_age(call: CallbackQuery, user: Users, session: AsyncSession):
    call_data = call.data.split(":")

    profile = await session.scalar(
        select(Profile)
        .where(Profile.user_id == call.from_user.id)
    )

    if len(call_data) == 3:
        profile.target_age = call_data[2]

    await call.message.edit_caption(
        caption=user_text.CHANGE_SEARCH_CHOOSE,
        reply_markup=user_kb.inline.change_search_age(
            target_age=json.loads(profile.target_age)
        )
    )


async def change_search_room(call: CallbackQuery, user: Users, session: AsyncSession):
    call_data = call.data.split(":")

    profile = await session.scalar(
        select(Profile)
        .where(Profile.user_id == call.from_user.id)
    )

    if len(call_data) == 3:
        profile.target_room = call_data[2]

        if call_data[2] == "Общая":
            profile.target_room = ""

    await call.message.edit_caption(
        caption=user_text.CHANGE_SEARCH_CHOOSE,
        reply_markup=user_kb.inline.change_search_room(
            target_room=profile.target_room or "Общая"
        )
    )


async def change_search_error(call: CallbackQuery, user: Users, session: AsyncSession):
    await call.message.answer(
        text=user_text.CHANGE_SEARCH_ERROR,
        reply_markup=user_kb.inline.offer_premium()
    )

    await change_search(call, user, session)


def register(router: Router):
    router.message.register(change_search, F.text == buttons.CHANGE_SEARCH)
    router.message.register(change_search, Command("search"))

    router.callback_query.register(change_search, F.data == "change_search")

    router.callback_query.register(
        change_search_error,
        F.data.startswith("change_search:gender:") |
        F.data.startswith("change_search:age:") |
        F.data.startswith("change_search:room:"),
        ~ IsVipFilter()
    )

    router.callback_query.register(change_search_gender, F.data.startswith("change_search:gender"))
    router.callback_query.register(change_search_age, F.data.startswith("change_search:age"))
    router.callback_query.register(change_search_room, F.data.startswith("change_search:room"))
