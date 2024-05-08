from contextlib import suppress

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select

from settings import SEND_EXCEPTIONS
from app.utils.callback_data import CreatePaymentCallbackFactory
from app.database.models import Profile, Users
from app.templates.texts import user as user_text
from app.templates.keyboards import user as user_kb


class GivePurchases:
    PURCHASES_TEXT = {
        "nullable_rate": "Обнуление рейтинга",
        "premium": "Покупка PREMIUM",
        "roulette": "Прокрутка рулетки"
    }

    def __init__(
        self,
        premium: CreatePaymentCallbackFactory,
        bot: Bot,
        session: AsyncSession
    ) -> None:
        self._premium = premium
        self._bot = bot
        self._session = session


    async def nullable_rate(self) -> None:
        await self._session.execute(
            update(Profile)
            .where(Profile.user_id == self._premium.user_id)
            .values(
                fire=0,
                satan=0,
                clown=0,
                shit=0
            )
        )

        with suppress(*SEND_EXCEPTIONS):
            await self._bot.send_message(
                chat_id=self._premium.user_id,
                text=user_text.DONE_NULLABLE_RATE
            )


    async def premium(self) -> None:
        user = await self._session.scalar(
            select(Users)
            .where(Users.user_id == self._premium.user_id)
        )

        user.add_vip(self._premium.days)

        with suppress(*SEND_EXCEPTIONS):
            await self._bot.send_message(
                chat_id=self._premium.user_id,
                text=user_text.GIVE_PREMIUM.format(
                    days=self._premium.days
                )
            )


    async def roulette(self) -> None:
        with suppress(*SEND_EXCEPTIONS):
            await self._bot.send_message(
                chat_id=self._premium.user_id,
                text=user_text.CASINO_START,
                reply_markup=user_kb.inline.casino()
            )
