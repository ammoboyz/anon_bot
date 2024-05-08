import asyncio
import time
from datetime import datetime, timedelta

from aiogram.fsm.context import FSMContext
from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from settings import VIP_OPTIONS
from app.templates.texts import buttons, user as user_text
from app.templates.keyboards import user as user_kb
from app.database.models import Users
from app.utils.callback_data import CreatePaymentCallbackFactory
from app.utils import (
    Settings,
    PremiumCallbackFactory,
    aaio_payment,
    func
)


async def premium(update: Message | CallbackQuery, bot: Bot, state: FSMContext):
    PHOTO_URL = "https://telegra.ph/file/4687f4410a726b1204aa8.png"

    msg_kwargs = {
        "caption": user_text.PREMIUM_INFO,
        "reply_markup": user_kb.inline.premium()
    }

    if isinstance(update, Message):
        await update.answer_photo(
            photo=PHOTO_URL,
            **msg_kwargs
        )

    elif isinstance(update, CallbackQuery):
        if update.message.caption:
            return await update.message.edit_caption(**msg_kwargs)

        await update.message.answer_photo(
            photo=PHOTO_URL,
            **msg_kwargs
        )

    fsm_data = await state.get_data()

    if fsm_data.get('time_discount', 0) > (time.time() - 60 * 60):
        return

    await asyncio.sleep(60 * 2)

    if fsm_data.get('time_discount', 0) > (time.time() - 60 * 60):
        return

    await bot.send_photo(
        chat_id=update.from_user.id,
        photo=PHOTO_URL,
        caption=user_text.PREMIUM_DISCOUNT.format(
            (datetime.now() + timedelta(hours=4 * 2)).strftime("%d.%m.%Y %H:%M:%S")
        ),
        reply_markup=user_kb.inline.premium_list(discount=40)
    )

    await state.update_data(
        time_discount=time.time()
    )


async def premium_list(call: CallbackQuery):
    PHOTO_URL = "https://telegra.ph/file/4687f4410a726b1204aa8.png"

    if call.message.caption:
        return await call.message.edit_caption(
            caption=user_text.PREMIUM_INFO,
            reply_markup=user_kb.inline.premium_list()
        )

    await call.message.answer_photo(
        photo=PHOTO_URL,
        caption=user_text.PREMIUM_INFO,
        reply_markup=user_kb.inline.premium_list()
    )


async def payment_create(
        call: CallbackQuery,
        config: Settings,
        callback_data: PremiumCallbackFactory
):
    buy = VIP_OPTIONS.get(callback_data.product)

    order_id = CreatePaymentCallbackFactory(
        user_id=call.from_user.id,
        pay_code=func.generate_random_code(),
        days=buy.get('days', 0),
        method_name=buy.get('method_name')
    ).pack()

    payment_url = await aaio_payment.create_payment_url(
        order_id=order_id,
        amount=callback_data.amount,
        config=config
    )

    caption = user_text.PAYMENT_CREATE.format(
        product=buy.get('msg_name'),
        amount=callback_data.amount,
        admin=config.bot.manager_link
    )

    if buy.get('method_name') == "roulette":
        caption = user_text.CASINO_DESCRIPTION

    await call.message.edit_caption(
        caption=caption,
        reply_markup=user_kb.inline.payment_create(
            callback_back=callback_data.callback_back,
            payment_url=payment_url
        )
    )


async def premium_free(update: CallbackQuery | Message, bot: Bot, user: Users):
    bot_info = await bot.get_me()

    type = ""

    if isinstance(update, CallbackQuery):
        if len(update.data.split(":")) > 1:
            type = update.data.split(":")[1]

    msg_kwargs = {
        "caption": user_text.PREMIUM_FREE.format(
            ref_count=user.referal_count,
            bot_username=bot_info.username,
            user_id=update.from_user.id
        ),
        "reply_markup": user_kb.inline.premium_free(
            bot_username=bot_info.username,
            user_id=update.from_user.id,
            skip_back=bool(type)
        )
    }

    if isinstance(update, CallbackQuery):
        await update.message.edit_caption(**msg_kwargs)

    elif isinstance(update, Message):
        await update.answer_photo(
            photo="https://telegra.ph/file/4687f4410a726b1204aa8.png",
            **msg_kwargs
        )


def register(router: Router):
    router.message.register(premium, F.text == buttons.PREMIUM)

    router.message.register(premium, Command("prem"))
    router.message.register(premium_free, Command("ref"))

    router.callback_query.register(premium, F.data == "premium")
    router.callback_query.register(premium_list, F.data == "premium_list")
    router.callback_query.register(premium_free, F.data.startswith("premium_free"))
    router.callback_query.register(payment_create, PremiumCallbackFactory.filter())
