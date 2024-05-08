import json

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from settings import SEND_EXCEPTIONS
from app.database.models import Shows, ViewsHistory


async def show_action(
        bot: Bot,
        user_id: int,
        state: FSMContext,
        session: AsyncSession,
        is_hello: bool = False
    ) -> None:
    fsm_data = await state.get_data()

    show_list = (await session.scalars(
        select(Shows)
        .where(Shows.is_actual == True)
        .where(Shows.is_hello == is_hello)
    )).all()

    if not show_list:
        return

    finish_show = None
    next_show = None

    for i in range(len(show_list)):
        if show_list[i].id == fsm_data.get('show_id', show_list[0].id) and show_list[i].is_actual:
            try:
                next_show = show_list[i + 1]
            except IndexError as e:
                next_show = show_list[0]

            finish_show = show_list[i]
            break
    else:
        finish_show = next_show = show_list[0]

    if finish_show is None:
        return

    try:
        await bot.copy_message(
            chat_id=user_id,
            from_chat_id=finish_show.from_chat_id,
            message_id=finish_show.message_id,
            reply_markup=(
                json.loads(finish_show.markup)
                if finish_show.markup else None
            )
        )
    except tuple(SEND_EXCEPTIONS) as e:
        return

    finish_show.views += 1

    if finish_show.views >= finish_show.views_limit:
        finish_show.is_actual = False

    new_view = ViewsHistory(
        sponsor_id=finish_show.id,
        user_id=user_id
    )

    await state.update_data(
        show_id=next_show.id,
    )

    await session.merge(new_view)
