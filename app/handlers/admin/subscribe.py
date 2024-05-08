import random

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from aiogram.utils.token import TokenValidationError
from aiogram import exceptions, Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database.models import Sponsors, Shows
from app.filters.states import AdminState
from app.templates.keyboards import admin as admin_kb
from app.utils import admin_func


async def sponsors_menu_one(call: CallbackQuery):
    await call.message.edit_text(
        text="<b>💸 Выберите тип партнёрства:</b>",
        reply_markup=admin_kb.inline.sponsors_type()
    )


async def sponsors_list(call: CallbackQuery, state: FSMContext, router: Router, session: AsyncSession):
    await state.set_state()

    sponsor_type = call.data.split(":")[1]
    sponsor_text = "показов" if sponsor_type == "show" else "ОП"

    await call.message.delete()
    await call.message.answer(
        text=f"<b>💸 Спонсорское меню {sponsor_text}:</b>",
        reply_markup=await admin_kb.inline.sponsors_list(session, router, sponsor_type)
    )


async def manage_sponsor(call: CallbackQuery, session: AsyncSession):
    sponsor_type, sponsor_id = call.data.split(":")[1:]
    sponsor_id = int(sponsor_id)

    sponsor = await session.scalar(
        select(Sponsors)
        .where(Sponsors.id == sponsor_id)
    )

    finish_text = admin_func.sponsor_get_info(sponsor)

    if sponsor.is_show:
        finish_text, pic = await admin_func.show_get_info(session, sponsor_id)
        await call.message.delete()
        return await call.message.answer_photo(
            photo=BufferedInputFile(
                file=pic.getvalue(),
                filename="stats.png"
            ),
            caption=finish_text,
            reply_markup=admin_kb.inline.sponsor_manage(sponsor_id, sponsor_type)
        )

    await call.message.edit_text(
        text=finish_text,
        reply_markup=admin_kb.inline.sponsor_manage(sponsor_id, sponsor_type)
    )


async def sponsor_approve(call: CallbackQuery, session: AsyncSession):
    sponsor_type, sponsor_id = call.data.split(":")[1:]
    sponsor_id = int(sponsor_id)

    sponsor = await session.scalar(
        select(Sponsors)
        .where(Sponsors.id == sponsor_id)
    )

    await call.message.delete()
    await call.message.answer(
        text=f"<b>🚮 Вы точно хотите удалить спонсора <a href='{sponsor.url}'>{sponsor.first_name}</a>?</b>",
        reply_markup=admin_kb.inline.sponsor_approve_delete(sponsor_id, sponsor_type),
        disable_web_page_preview=True
    )


async def sponsor_delete(call: CallbackQuery, session: AsyncSession):
    sponsor_type, sponsor_id = call.data.split(":")[1:]
    sponsor_id = int(sponsor_id)

    sponsor = await session.scalar(
        select(Sponsors)
        .where(Sponsors.id == sponsor_id)
    )

    if sponsor.is_show:
        await session.execute(
            delete(Shows)
            .where(Shows.id == sponsor_id)
        )

    await session.execute(
        delete(Sponsors)
        .where(Sponsors.id == sponsor_id)
    )

    await call.message.edit_text(
        text=f"<b>✅ Cпонсор <a href='{sponsor.url}'>{sponsor.first_name}</a> успешно удалён.</b>",
        reply_markup=admin_kb.inline.go_back(f"sponsors_list:{sponsor_type}"),
        disable_web_page_preview=True
    )


async def add_sponsor_choose(call: CallbackQuery):
    sponsor_type = call.data.split(":")[1]

    await call.message.edit_text(
        text="<b>👥 Выбери кого добавить:</b>",
        reply_markup=admin_kb.inline.sponsor_choose(sponsor_type)
    )


async def add_channel(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.sub_add_channel_1)
    await call.message.edit_text(
        text="<b>👥 Перешли сообщение из тг канала.\n\nЕсли вы хотите поставить чат на ОП, отправьте его ID используя @username_to_id_bot</b>",
        reply_markup=admin_kb.inline.go_back("sponsors_list:op")
    )


async def add_channel_forwarded(message: Message, state: FSMContext, bot: Bot):
    if message.text and not message.text.replace("-", "").isdigit():
        try:
            channel_id = int(message.text)
            chat_info = await bot.get_chat(
                chat_id=channel_id
            )
            first_name = chat_info.full_name
        except Exception as e:
            return await message.answer(
                text=f"<b>👥 Чат не найден!</b>\n\n<i>Пожалуйста, добавьте бота в чат как администратора.</i>",
                reply_markup=admin_kb.inline.go_back("sponsors_list:op")
            )
    else:
        try:
            channel_id = message.forward_from_chat.id
            first_name = message.forward_from_chat.title
        except Exception as e:
            return await message.answer(
                text=f"<b>👥 Сообщение переслано не из канала❗️</b>",
                reply_markup=admin_kb.inline.go_back("sponsors_list:op")
            )

    await state.update_data(
        channel_id=channel_id,
        first_name=str(first_name)
    )
    await state.set_state(AdminState.sub_add_channel_2)

    await message.answer(
        text="<b>👥 Теперь отправьте ссылку приглашения в канал/чат.</b>",
        reply_markup=admin_kb.inline.go_back("sponsors_list:op")
    )


async def add_channel_url(message: Message, state: FSMContext, session: AsyncSession):
    entities = message.entities
    url = ''

    for item in entities:
        if item.type == "url":
            url = message.text[item.offset:item.offset+item.length]

    if url == '':
        return await message.answer(
            text="<b>👥 Вы не отправляли ссылку❗️</b>",
            reply_markup=admin_kb.inline.go_back("sponsors_list:op")
        )

    fsm_data = await state.get_data()
    channel_id = fsm_data["channel_id"]
    first_name = fsm_data["first_name"]

    new_sponsor = Sponsors(
        id=channel_id,
        first_name=first_name,
        url=url,
        is_bot=False,
        token=""
    )
    await session.merge(new_sponsor)

    await message.answer(
        text=f"<b>✅ Канал <a href='{url}'>{first_name}</a> успешно добавлен!</b>",
        reply_markup=admin_kb.inline.go_back("sponsors_list:op"),
        disable_web_page_preview=True
    )


async def add_bot(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.sub_add_bot_1)
    await call.message.edit_text(
        text="<b>👥 Отправьте токен бота.</b>",
        reply_markup=admin_kb.inline.go_back("sponsors_list:op")
    )


async def add_bot_token(message: Message, state: FSMContext):
    try:
        bot_inistance = Bot(message.text)
        bot_info = await bot_inistance.get_me()
    except TokenValidationError:
        return await message.answer(
            text="<b>❌ Токен бота недействителен!</b>",
            reply_markup=admin_kb.inline.go_back("sponsors_list:op"))
    except exceptions.TelegramUnauthorizedError:
        return await message.answer(
            text="<b>❌ Токен бота неправильно написан! Пожалуйста, попробуйте его заменить.</b>",
            reply_markup=admin_kb.inline.go_back("sponsors_list:op")
        )
    finally:
        await bot_inistance.session.close()

    first_name = bot_info.first_name
    username = bot_info.username
    bot_id = bot_info.id

    await state.update_data(
        first_name=first_name,
        bot_id=bot_id,
        token=message.text
    )
    await state.set_state(AdminState.sub_add_bot_2)

    await message.answer(
        text=f"<b>👥 Найден бот <a href='https://t.me/{username}'>{first_name}</a></b>\n\n"
        "ℹ️ Теперь отправьте ссылку на бота.",
        reply_markup=admin_kb.inline.go_back("sponsors_list:op"),
        disable_web_page_preview=True
    )


async def add_bot_url(message: Message, state: FSMContext, session: AsyncSession):
    entities = message.entities
    url = ''

    for item in entities:
        if item.type == "url":
            url = message.text[item.offset:item.offset+item.length]

    if url == '':
        return await message.answer(
            text="<b>👥 Вы не отправляли ссылку❗️</b>",
            reply_markup=admin_kb.inline.go_back("sponsors_list:op")
        )

    fsm_data = await state.get_data()

    first_name = fsm_data['first_name']
    bot_id = fsm_data['bot_id']
    token = fsm_data['token']

    new_sponsor = Sponsors(
        id=bot_id,
        first_name=first_name,
        token=token,
        is_bot=True,
        url=url
    )
    await session.merge(new_sponsor)

    await message.answer(
        text=f"<b>✅ Бот <a href='{url}'>{first_name}</a> успешно добавлен!</b>",
        reply_markup=admin_kb.inline.go_back("sponsors_list:op"),
        disable_web_page_preview=True
    )


async def add_show(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.sub_add_show_1)

    await call.message.edit_text(
        text="<b>📣 Отправьте название для рекламы:</b>",
        reply_markup=admin_kb.inline.go_back("sponsors_list:show")
    )


async def add_show_name(message: Message, state: FSMContext):
    await state.update_data(
        show_name=message.text
    )

    await state.set_state(AdminState.sub_add_show_2)

    await message.answer(
        text="<b>📣 Отправьте числом лимит на данную рекламу.</b>",
        reply_markup=admin_kb.inline.go_back("sponsors_list:show")
    )


async def add_show_limit(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer(
            text="<b>📣 Введите число!</b>",
            reply_markup=admin_kb.inline.go_back("sponsors_list:show")
        )

    await state.update_data(
        show_limit=int(message.text)
    )

    await message.answer(
        text="<b>📣 Выбери тип данного показа:</b>",
        reply_markup=admin_kb.inline.show_type()
    )


async def add_show_type(call: CallbackQuery, state: FSMContext):
    show_type = call.data.split(":")[1]

    await state.update_data(
        is_hello=True if show_type == "hello" else False
    )

    await state.set_state(AdminState.sub_add_show_3)

    await call.message.edit_text(
        text=f"<b>📣 Отправьте рекламный пост:</b>",
        reply_markup=admin_kb.inline.go_back("sponsors_list:show")
    )


async def add_show_post(message: Message, state: FSMContext, session: AsyncSession):
    fsm_data = await state.get_data()

    if message.reply_markup:
        show_markup = message.reply_markup.model_dump_json()
    else:
        show_markup = ""

    sponsor_id = random.randint(1,1000000000)

    sponsor_new = Sponsors(
        id=sponsor_id,
        first_name=fsm_data.get('show_name'),
        is_show=True
    )

    show_new = Shows(
        id=sponsor_id,
        name=fsm_data.get('show_name'),
        from_chat_id=message.chat.id,
        message_id=message.message_id,
        views_limit=fsm_data.get('show_limit'),
        markup=str(show_markup),
        is_hello=fsm_data.get('is_hello', False)
    )

    await session.merge(sponsor_new)
    await session.merge(show_new)

    await state.set_state()
    await message.answer(
        text=f"<b>📣✅ Рекламный пост {show_new.name} успешно установлен на показы!</b>",
        reply_markup=admin_kb.inline.go_back("sponsors_list:show")
    )


def register(router: Router):
    router.callback_query.register(sponsors_menu_one, F.data == "sponsors_menu")
    router.callback_query.register(sponsors_list, F.data.startswith("sponsors_list:"))
    router.callback_query.register(add_sponsor_choose, F.data == "add_sponsor:op")

    router.callback_query.register(manage_sponsor, F.data.startswith("manage_sponsor:"))
    router.callback_query.register(sponsor_approve, F.data.startswith("sponsor_approve:"))
    router.callback_query.register(sponsor_delete, F.data.startswith("sponsor_delete:"))

    router.callback_query.register(add_bot, F.data == "add_bot")
    router.message.register(add_bot_token, F.text, StateFilter(AdminState.sub_add_bot_1))
    router.message.register(add_bot_url, F.text, StateFilter(AdminState.sub_add_bot_2))

    router.callback_query.register(add_channel, F.data == "add_channel")
    router.message.register(add_channel_forwarded, StateFilter(AdminState.sub_add_channel_1))
    router.message.register(add_channel_url, F.entities, StateFilter(AdminState.sub_add_channel_2))

    router.callback_query.register(add_show, F.data == "add_sponsor:show")
    router.message.register(add_show_name, F.text, StateFilter(AdminState.sub_add_show_1))
    router.message.register(add_show_limit, F.text, StateFilter(AdminState.sub_add_show_2))
    router.callback_query.register(add_show_type, F.data.startswith("show_type:"))
    router.message.register(add_show_post, StateFilter(AdminState.sub_add_show_3))
