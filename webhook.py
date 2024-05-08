import logging as lg
from datetime import datetime
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, Redis

from fastapi import FastAPI, Form, Depends

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.engine import URL
from sqlalchemy import select

from app.templates.texts import admin as admin_text
from app.database.models import Base, BuyHistory, Users
from app.utils.give_purchases import GivePurchases
from app.utils.callback_data import CreatePaymentCallbackFactory
from app.utils import (
    load_config,
    Settings
)
from settings import BOT_TOKEN, DB_NANE


lg.basicConfig(level=lg.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
app = FastAPI()


# Aiogram 3
config: Settings = load_config()
redis: Redis = Redis(host='redis')
storage: RedisStorage = RedisStorage(redis=redis)
dp: Dispatcher = Dispatcher(storage=storage)
bot: Bot = Bot(
    token=BOT_TOKEN,
    parse_mode="HTML"
)


# SQLALCHEMY
engine = create_async_engine(
    URL(
        'postgresql+asyncpg',
        config.db.user,
        config.db.password,
        config.db.host,
        config.db.port,
        DB_NANE,
        query={},
    ),
    future=True
)
SessionLocal = async_sessionmaker(engine)


async def get_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session = SessionLocal()
    try:
        yield session
    finally:
        await session.commit()
        await session.close()


@app.post("/pay/payment")
async def payment(
    order_id: str = Form(),
    amount: float = Form(),
    currency: str = Form(),
    session: AsyncSession = Depends(get_db)
):
    lg.info(order_id)
    premium = CreatePaymentCallbackFactory.unpack(order_id)
    user_info = await bot.get_chat_member(
        chat_id=premium.user_id,
        user_id=premium.user_id
    )

    give_purchases = GivePurchases(premium, bot, session)
    purchases_method = getattr(give_purchases, premium.method_name, None)

    if not purchases_method or not callable(purchases_method):
        raise AttributeError(f"Method {premium.method_name} not found or not callable")

    await purchases_method()

    user = await session.scalar(
        select(Users)
        .where(Users.user_id == premium.user_id)
    )

    new_buy = BuyHistory(
        user_id=premium.user_id,
        amount=amount,
        pay_code=premium.pay_code,
        where_from=user.where_from
    )

    await session.merge(new_buy)

    # with suppress(*SEND_EXCEPTIONS)
    await bot.send_message(
        chat_id=config.bot.admin_chat,
        text=admin_text.PREMIUM_REPORT.format(
            username=user_info.user.username,
            product=give_purchases.PURCHASES_TEXT.get(premium.method_name, "неизвестно"),
            amount=amount,
            date=datetime.now().strftime("%d.%m.%Y"),
            currency=currency
        )
    )

    return 200
