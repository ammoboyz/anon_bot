from aiogram import F, Router, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters import NoneRegisterFilter
from app.database.models import Users
from app.templates.texts import user as user_text
from app.templates.keyboards import user as user_kb
from .start import call_start


async def gender(call: CallbackQuery, user: Users, state: FSMContext):
    sex = call.data.split(":")[1]
    user.is_man = True if sex == "man" else False

    await call.message.edit_caption(
        caption=user_text.CHANGE_AGE,
        reply_markup=user_kb.inline.change_age()
    )


async def age(
        call: CallbackQuery,
        user: Users,
        state: FSMContext,
        session: AsyncSession,
        bot: Bot
    ):
    user.age = int(call.data.split(":")[1])

    await call_start(call, bot, state, user, session, True)

def register(router: Router):
    router.callback_query.register(gender, F.data.startswith("choise_sex_none_reg:"), NoneRegisterFilter())
    router.callback_query.register(age, F.data.startswith("add_age:"), NoneRegisterFilter())
