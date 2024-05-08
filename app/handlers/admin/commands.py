from datetime import datetime

from aiogram import F, Router, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Users
from app.filters import IsAdmin
from app.utils import func


async def add_vip(message: Message, session: AsyncSession):
    split_text = message.text.split()

    if len(split_text) != 3:
        return await message.answer(
            text="<b>⚠️ Неправильный формат команды!</b>\n\n<code>/add_vip ID days</code>"
        )

    if not split_text[2].isdigit() or not split_text[1].isdigit():
        return await message.answer(
            text="<b>⚠️ Неправильный формат ID или days!</b>"
        )

    user_instance = await session.scalar(
        select(Users)
        .where(Users.user_id == int(split_text[1]))
    )

    if user_instance is None:
        return await message.answer(
            text="<b>⚠️ Данный ID не найден в базе данных!</b>"
        )

    user_instance.add_vip(int(split_text[2]))

    await message.answer(
        text=f"<b>✅ Пользователю c ID {user_instance.user_id} выдан VIP на {split_text[2]} дней.</b>"
    )


async def check_user(message: Message, bot: Bot, session: AsyncSession):
    split_text = message.text.split()

    if len(split_text) != 2:
        return await message.answer(
            text="<b>⚠️ Неправильный формат команды!</b>\n\n<code>/check_user ID</code>"
        )

    if not split_text[1].isdigit():
        return await message.answer(
            text="<b>⚠️ Неправильный формат ID</b>"
        )

    user_instance = await session.scalar(
        select(Users)
        .where(Users.user_id == int(split_text[1]))
    )

    if user_instance is None:
        return await message.answer(
            text="<b>⚠️ Данный ID не найден в базе данных!</b>"
        )

    user_info = await bot.get_chat_member(
        chat_id=user_instance.user_id,
        user_id=user_instance.user_id
    )

    await message.answer(
        text=f'''
<b>👨‍🦱 Пользователь:</b> @{user_info.user.username}
<b>✍️ Полное имя:</b> <code>{user_info.user.first_name}</code>
<b>🤴 Премиум:</b> <code>{"да" if user_info.user.is_premium else "нет"}</code>

<b>🆔 ID:</b> <code>{user_instance.user_id}</code>
<b>🗓 Зарегистрирован: </b> <code>{user_instance.reg_date}</code>
<b>☠️ Мёртв:</b> <code>{"да" if user_instance.dead else "нет"}</code>
<b>⛔️ Забанен:</b> <code>{"да" if user_instance.banned else "нет"}</code>

<b>👑 VIP:</b> <code>{func.days_until(user_instance.vip_time) if user_instance.vip_time else "нет"}</code>
'''
    )


async def delete_vip(message: Message, session: AsyncSession):
    split_text = message.text.split()

    if len(split_text) != 2:
        return await message.answer(
            text="<b>⚠️ Неправильный формат команды!</b>\n\n<code>/delete_vip ID</code>"
        )

    if not split_text[1].isdigit():
        return await message.answer(
            text="<b>⚠️ Неправильный формат ID</b>"
        )

    user_instance = await session.scalar(
        select(Users)
        .where(Users.user_id == int(split_text[1]))
    )

    if user_instance is None:
        return await message.answer(
            text="<b>⚠️ Данный ID не найден в базе данных!</b>"
        )

    user_instance.vip_time = datetime(1970, 1, 1)

    await message.answer(
        text=f"<b>✅ У пользователя c ID {user_instance.user_id} успешно удалён VIP!</b>"
    )


async def ban(call: CallbackQuery, session: AsyncSession):
    user_id = int(call.data.split(":")[1])

    await session.execute(
        update(Users)
        .where(Users.user_id == user_id)
        .values(banned=True)
    )

    await call.message.delete()

    await call.message.answer(
        text=f"<b>✅ Пользователь c ID <code>{user_id}</code> забанен</b>"
    )


async def ban_command(message: Message, session: AsyncSession):
    split_text = message.text.split()

    if len(split_text) != 2:
        return await message.answer(
            text="<b>⚠️ Неправильный формат команды!</b>\n\n<code>/ban ID</code>"
        )

    user_id = int(split_text[1])

    await session.execute(
        update(Users)
        .where(Users.user_id == user_id)
        .values(banned=True)
    )

    await message.answer(
        text=f"<b>✅ Пользователь c ID <code>{user_id}</code> забанен</b>"
    )


async def unban_command(message: Message, session: AsyncSession):
    split_text = message.text.split()

    if len(split_text) != 2:
        return await message.answer(
            text="<b>⚠️ Неправильный формат команды!</b>\n\n<code>/unban ID</code>"
        )

    user_id = int(split_text[1])

    await session.execute(
        update(Users)
        .where(Users.user_id == user_id)
        .values(banned=False)
    )

    await message.answer(
        text=f"<b>✅ Пользователь c ID <code>{user_id}</code> разбанен</b>"
    )


def register(router: Router):
    router.message.register(add_vip, Command("add_vip"), IsAdmin())
    router.message.register(check_user, Command("check_user"), IsAdmin())
    router.message.register(delete_vip, Command("delete_vip"), IsAdmin())
    router.callback_query.register(ban, F.data.startswith("ban:"), IsAdmin())
    router.message.register(ban_command, Command("ban"), IsAdmin())
    router.message.register(unban_command, Command("unban"), IsAdmin())