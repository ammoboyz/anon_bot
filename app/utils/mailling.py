import asyncio

from aiogram.types import InlineKeyboardMarkup, CallbackQuery
from aiogram import exceptions, Bot
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, delete

from app.database.models import Users, Chats
from settings import SEND_EXCEPTIONS


class AiogramMailling:
    def __init__(
            self,
            list_id: list[int | str],
            bot: Bot,
            call: CallbackQuery,
            session: AsyncSession,
            mailling_id: int,
            mailling_markup: dict | list,
            finally_markup: list,
            is_media: bool = True,
            caption: str = "",
            chunk_size: int = 30
        ):

        self.message_id = mailling_id
        self.caption = caption
        self.reply_markup = mailling_markup
        self.call = call
        self.is_media = is_media

        self.session = session
        self.bot = bot
        self.list_id = list_id
        self.finally_markup = finally_markup
        self.chunk_size = chunk_size

        self.dead_list = []
        self.good_list = []
        self.mailling_status = False
        self.mailling_second = 0


    @staticmethod
    def _divide_list(
            main_list: list[int | str],
            chunk_size: int) -> list[list[int | str]]:

        splitted_list = []

        for i in range(0, len(main_list), chunk_size):
            splitted_list.append(main_list[i:i+chunk_size])

        return splitted_list


    async def _mailling_cycle(self, list_id: list):
        for chat_id in list_id:
            if not self.mailling_status:
                return

            result = await self._send_message(chat_id)
            if not result:
                self.dead_list.append(chat_id)
            else:
                self.good_list.append(chat_id)


    async def _mailling_monitor(self) -> None:
        await asyncio.sleep(1)
        while self.mailling_status:
            try:
                await self.call.message.edit_text(
                    text="<b>✉️ Идёт рассылка!</b>\n\n"
                    f"✅ Успешно отправлено: <code>{len(self.good_list)}</code>\n"
                    f"❌ Не отправлено: <code>{len(self.dead_list)}</code>\n"
                    f"🕘 Прошло секунд: <code>{self.mailling_second}</code>",
                )
            except exceptions.TelegramRetryAfter as e:
                self.mailling_second += e.retry_after
                await asyncio.sleep(e.retry_after)
            self.mailling_second += 5
            await asyncio.sleep(5)


    async def _send_message(self, chat_id: int):
        try:
            if self.call.from_user.id == chat_id:
                return True

            try:
                user_info = await self.bot.get_chat_member(
                    chat_id=chat_id,
                    user_id=chat_id
                )
                full_name = user_info.user.full_name
                username = user_info.user.username
            except tuple(SEND_EXCEPTIONS) as e:
                full_name = "Привет"
                username = "Привет"

            finish_caption = self.caption.format(
                full_name=full_name,
                username=username
            )

            if self.is_media:
                await self.bot.copy_message(
                    chat_id=chat_id,
                    caption=finish_caption,
                    message_id=self.message_id,
                    from_chat_id=self.call.message.chat.id,
                    reply_markup=self.reply_markup
                )

            else:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=finish_caption,
                    reply_markup=self.reply_markup
                )
        except exceptions.TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            return await self._send_message(chat_id)
        except Exception as e:
            return False
        else:
            return True


    async def mailling_process(self):
        divided_list_id = self._divide_list(self.list_id, self.chunk_size)
        tasks = []
        self.mailling_status = True

        await self.call.message.edit_text(
            text="<b>🔥 Рассылка начата!</b>",
            parse_mode="HTML"
        )

        asyncio.create_task(self._mailling_monitor())

        for list_id in divided_list_id:
            task = asyncio.create_task(self._mailling_cycle(list_id))
            tasks.append(task)
        await asyncio.gather(*tasks)

        self.mailling_status = False

        await self.session.execute(
            update(Users)
            .where(Users.user_id.in_(self.dead_list))
            .values({Users.dead: True})
        )

        await self.session.execute(
            delete(Chats)
            .where(Chats.chat_id.in_(self.dead_list))
        )

        await self.call.message.edit_text(
            text="<b>✉️ Рассылка завершена!</b>\n\n"
            f"✅ Успешно отправлено: <code>{len(self.good_list)}</code>\n"
            f"❌ Не отправлено: <code>{len(self.dead_list)}</code>\n"
            f"🕘 Прошло секунд: <code>{self.mailling_second}</code>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=self.finally_markup))
