import os
import asyncio
import aiocron
import logging

from app import middlewares, handlers
from app.database import create_sessionmaker
from app.utils import load_config, func
from settings import BOT_TOKEN

from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.redis import RedisStorage, Redis


log = logging.getLogger(__name__)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logging.getLogger(
        'aiogram.event',
    ).setLevel(logging.WARNING)

    log.info("Starting bot...")
    config = load_config()

    os.environ['TZ'] = config.bot.timezone

    log.info('Set timesone to "%s"' % config.bot.timezone)

    redis: Redis = Redis(host='redis')
    storage: RedisStorage = RedisStorage(redis=redis)
    sessionmaker = await create_sessionmaker(config.db)

    bot = Bot(
        token=BOT_TOKEN,
        parse_mode="HTML"
    )
    dp = Dispatcher(storage=storage)

    middlewares.setup(dp, sessionmaker)
    handlers.setup(dp, config)

    bot_info = await bot.me()
    await bot.delete_webhook(drop_pending_updates=True)

    router = Router()
    dp.include_router(router)

    aiocron.crontab(
        spec='0 20 * * 0',
        func=func.lottery,
        args=(sessionmaker, bot),
        start=False
    )

    aiocron.crontab(
        spec="0 * * * *",
        func=func.backup,
        args=(sessionmaker, bot, config),
        start=True
    )

    try:
        await dp.start_polling(
            bot,
            router=router,
            config=config,
            dp=dp,
            bot_info=bot_info,
            allowed_updates=[
                "message",
                "callback_query",
                "my_chat_member"
            ]
        )
    finally:
        await dp.fsm.storage.close()


try:
    asyncio.run(main())
except (
    KeyboardInterrupt,
    SystemExit,
):
    log.critical("Bot stopped")
