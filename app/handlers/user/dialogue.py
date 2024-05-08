import json
import io
from typing import Optional
from contextlib import suppress
from datetime import datetime

from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command
from aiogram import Router, Bot, F, Dispatcher
from aiogram.fsm.context import FSMContext

from sqlalchemy import delete, or_, select
from sqlalchemy.future import select as select_
from sqlalchemy.ext.asyncio import AsyncSession

from settings import SEND_EXCEPTIONS
from app.utils import show_action, func
from app.filters import InDialogueFilter, InQueueFilter
from app.database.models import Users, Queue, Dialogues, Profile
from app.templates.texts import buttons, user as user_text
from app.templates.keyboards import user as user_kb
from app.utils.config import Settings


async def warning_not_vip(bot: Bot, user_id: int, text: str):
    await bot.send_photo(
        chat_id=user_id,
        photo="https://telegra.ph/file/4687f4410a726b1204aa8.png",
        caption=user_text.NOT_VIP.format(text),
        reply_markup=user_kb.inline.offer_premium()
    )


async def queue(
        bot: Bot,
        dp: Dispatcher,
        session: AsyncSession,
        user: Users,
        profile: Profile,
        target_man: Optional[bool] = None
    ):
    stmt = select_(Queue) \
        .where(Queue.user_id != user.user_id) \
        .where(Queue.room == profile.target_room) \
        .where(
            Queue.age.in_(json.loads(profile.target_age))
            if profile.target_age != "[]" else True
        ) \
        .where(
            or_(
                Queue.target_man == user.is_man,
                Queue.target_man == None
            ),
        )

    if target_man is not None:
        stmt = stmt.where(Queue.is_man == target_man)

    elif profile.target_man is not None:
        stmt = stmt.where(Queue.is_man == profile.target_man)

    match = await session.scalar(stmt)

    if match:
        return await create_dialogue(bot, session, dp, user.user_id, match.user_id)

    await session.execute(
        delete(Queue)
        .where(Queue.user_id == user.user_id)
    )

    session.add(
        Queue(
            user_id=user.user_id,
            is_man=user.is_man,
            target_man=target_man,
            age=user.age,
            room=profile.target_room

        )
    )


    await bot.send_message(
        chat_id=user.user_id,
        text=user_text.DIALOGUE_SEARCH
    )


async def create_dialogue(
        bot: Bot,
        session: AsyncSession,
        dp: Dispatcher,
        first: int,
        second: int
    ):
    for user_id in (first, second):
        id_instance = first if user_id == second else second

        state_instance = await func.state_with(user_id, bot, dp)

        await state_instance.update_data(
            message_count=0,
            ban_words_count=0,
            msg_list=[]
        )

        first_user = await session.scalar(
            select(Users)
            .where(Users.user_id == user_id)
        )

        second_user = await session.scalar(
            select(Users)
            .where(Users.user_id == id_instance)
        )

        second_profile = await session.scalar(
            select(Profile)
            .where(Profile.user_id == id_instance)
        )

        gender_str = (
            ("М 🧑🏻" if second_user.is_man else "Д 👩🏼")
            if first_user.is_vip else "***"
        )

        age_str = (
            second_user.age if first_user.is_vip else "***"
        )

        vip_str = (
            "\n\n<b>Данный пользовать обладает 💎 PREMIUM</b>"
            if second_user.is_vip else ""
        )

        with suppress(*SEND_EXCEPTIONS):
            await bot.send_message(
                chat_id=user_id,
                text=user_text.DIALOGUE_FOUND.format(
                    is_vip=vip_str,
                    gender=gender_str,
                    age=age_str,
                    interests=', '.join(json.loads(second_profile.interests)) or "не указаны",
                    fire=second_profile.fire,
                    satan=second_profile.satan,
                    clown=second_profile.clown,
                    shit=second_profile.shit
                ),
                reply_markup=user_kb.reply.dialogue()
            )

    await session.execute(
        delete(Queue)
        .where(Queue.user_id.in_((first, second)))
    )

    session.add(
        Dialogues(
            first=first,
            second=second,
        )
    )


async def finish_dialogue(
        update: Message | CallbackQuery,
        bot: Bot,
        dp: Dispatcher,
        session: AsyncSession,
        user: Users
    ):
    dialogue = await Dialogues.get_dialogue(
        user_id=update.from_user.id,
        session=session
    )

    await session.execute(
        delete(Queue)
        .where(Queue.user_id == user.user_id)
    )

    if dialogue is None:
        return await bot.send_message(
            chat_id=update.from_user.id,
            text=user_text.SEARCH_END,
            reply_markup=user_kb.reply.start()
        )

    for user_id in [update.from_user.id, dialogue.second_id(update.from_user.id)]:
        user_db_instance = await session.scalar(
            select(Users)
            .where(Users.user_id == user_id)
        )

        profile_db_instance = await session.scalar(
            select(Profile)
            .where(Profile.user_id == user_id)
        )
        state_instance = await func.state_with(
            chat_id=user_id,
            bot=bot,
            dp=dp
        )
        fsm_data = await state_instance.get_data()

        time_in_dialogue = int((datetime.now() - dialogue.start_dialogue).total_seconds())
        profile_db_instance.time_in_chats += time_in_dialogue
        profile_db_instance.dialogue_count += 1
        profile_db_instance.swear_count += fsm_data.get('ban_words_count', 0)
        profile_db_instance.message_count += fsm_data.get('message_count', 0)

        with suppress(*SEND_EXCEPTIONS):
            await bot.send_message(
                chat_id=user_id,
                text=user_text.DIALOGUE_END,
                reply_markup=user_kb.reply.start()
            )

        with suppress(*SEND_EXCEPTIONS):
            await bot.send_message(
                chat_id=user_id,
                text=user_text.SEND_FEEDBACK.format(
                    second=time_in_dialogue,
                    message_count=fsm_data.get('message_count', 0),
                    bad_count=fsm_data.get('ban_words_count', 0)
                ),
                reply_markup=user_kb.inline.send_feedback(
                    user_id=dialogue.second_id(user_id)
                )
            )

        if not user_db_instance.is_vip:
            await show_action(bot, user_id, state_instance, session)

    await dialogue.delete_dialogue(
        session=session,
        user_id=update.from_user.id
    )


async def random_normal(
        _,
        bot: Bot,
        session: AsyncSession,
        dp: Dispatcher,
        profile: Profile,
        user: Users
    ):

    await queue(bot, dp, session, user, profile)


async def male_normal(
        message: Message,
        bot: Bot,
        dp: Dispatcher,
        session: AsyncSession,
        state: FSMContext,
        user: Users,
        profile: Profile
    ):
    if not user.is_vip:
        return await warning_not_vip(bot, message.from_user.id, "Поиск по полу доступен")

    await finish_dialogue(message, bot, dp, session, user)

    await queue(bot, dp, session, user, profile, True)


async def female_normal(
        message: Message,
        bot: Bot,
        dp: Dispatcher,
        session: AsyncSession,
        state: FSMContext,
        user: Users,
        profile: Profile
    ):
    if not user.is_vip:
        return await warning_not_vip(bot, message.from_user.id, "Поиск по полу доступен")

    await finish_dialogue(message, bot, dp, session, user)

    await queue(bot, dp, session, user, profile, False)



async def message_copy_to(
        message: Message,
        session: AsyncSession,
        user: Users,
        bot: Bot,
        dp: Dispatcher,
        state: FSMContext
    ):
    fsm_data = await state.get_data()
    dialogue = await Dialogues.get_dialogue(
        user_id=message.from_user.id,
        session=session
    )

    partner_id = dialogue.second_id(message.from_user.id)

    await state.update_data(
        message_count=fsm_data.get('message_count', 0) + 1,
        ban_words_count=(
            fsm_data.get('ban_words_count', 0) +
            func.check_ban_words(message.text or "")
        )
    )

    if message.text:
        entities = message.entities or []
        for item in entities:
            if item.type == "url":
                return await message.answer(
                    text=user_text.LINKS_ARE_PROHIBITED
                )

    if not message.text:
        if not user.is_vip:
            return await warning_not_vip(bot, message.from_user.id, "Обмен медиа")

    partner_state = await func.state_with(partner_id, bot, dp)
    partner_fsm_data = await partner_state.get_data()
    new_msg_list: list = partner_fsm_data.get('msg_list', [])

    if message.text:
        new_msg_list.append(message.text)
    elif message.caption:
        new_msg_list.append(message.caption)
    else:
        new_msg_list.append("Неизвестное медиа")

    await partner_state.update_data(
        msg_list=new_msg_list
    )

    try:
        await message.copy_to(
            chat_id=partner_id,
            reply_markup=user_kb.reply.dialogue()
        )
    except tuple(SEND_EXCEPTIONS) as e:
        await finish_dialogue(message, bot, dp, session, user)


async def already_search_dialogue(message: Message):
    await message.answer(
        text=user_text.ALREADY_SEARCH
    )


async def next(
        update: Message | CallbackQuery,
        bot: Bot,
        dp: Dispatcher,
        state: FSMContext,
        session: AsyncSession,
        user: Users,
        profile: Profile
    ):
    if await Dialogues.get_dialogue(update.from_user.id, session):
        await finish_dialogue(update, bot, dp, session, user)

    await queue(
        bot=bot,
        session=session,
        dp=dp,
        user=user,
        profile=profile
    )


async def send_feedback(call: CallbackQuery, session: AsyncSession):
    feedback_name, user_id = call.data.split(":")[1:]

    profile = await session.scalar(
        select(Profile)
        .where(Profile.user_id == int(user_id))
    )

    feedback_count = getattr(
        profile,
        feedback_name
    )

    setattr(profile, feedback_name, feedback_count + 1)

    await call.message.edit_reply_markup(
        reply_markup=user_kb.inline.send_feedback(
            user_id=profile.user_id,
            feedback_sended=True
        )
    )


async def report(call: CallbackQuery, state: FSMContext, bot: Bot, config: Settings):
    report_id = int(call.data.split(":")[1])

    await call.message.edit_text(
        text=user_text.REPORT_SENDED
    )

    user_info = await bot.get_chat_member(
        chat_id=report_id,
        user_id=report_id
    )

    fsm_data = await state.get_data()

    memory_buffer = io.BytesIO()
    for msg in fsm_data.get('msg_list', []):
        memory_buffer.write(str(msg).replace("\n", " ").encode('utf-8') + b"\n")

    memory_buffer.seek(0)

    input_file = BufferedInputFile(
        file=memory_buffer.getvalue(),
        filename=f"{report_id}.txt"
    )

    await bot.send_document(
        chat_id=config.bot.report_chat,
        document=input_file,
        caption=f"<b>‼️Пришёл репорт на ID <code>{report_id}</code></b>\n@{user_info.user.username}\n"
                f"Его сообщения находятся в документе ниже\n\n"
                f"Пришёл от @{call.from_user.username}\n"
                f"ID: <code>{call.from_user.id}</code>",
        reply_markup=user_kb.inline.report(user_id=report_id)
    )


async def previous(call: CallbackQuery, user: Users, bot: Bot):
    if not user.is_vip:
        return await warning_not_vip(bot, call.from_user.id, "Диалог с предыдущим собеседником доступен")

    await dialogue_request(call, bot)


async def friend_request(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    dialogue = await Dialogues.get_dialogue(message.from_user.id, session)
    second_id = dialogue.second_id(message.from_user.id)

    with suppress(*SEND_EXCEPTIONS):
        await bot.send_message(
            chat_id=second_id,
            text=user_text.FRIEND_RESPONSE,
            reply_markup=user_kb.inline.user_request(
                request_type="friend_request",
                user_id=message.from_user.id
            )
        )

    await message.answer(
        text=user_text.FRIEND_REQUEST
    )


async def friend_response(call: CallbackQuery, session: AsyncSession, bot: Bot):
    answer, second_id = call.data.split(":")[1:]
    second_id = int(second_id)

    if answer == "false":
        await call.message.edit_text(
            text=user_text.FRIEND_RESPONSE_FALSE
        )

        return await bot.send_message(
            chat_id=second_id,
            text=user_text.FRIEND_RESPONSE_FALSE
        )

    first_profile = await session.scalar(
        select(Profile)
        .where(Profile.user_id == call.from_user.id)
    )

    second_profile = await session.scalar(
        select(Profile)
        .where(Profile.user_id == second_id)
    )

    for profile in (first_profile, second_profile):
        profile_friends_list: list = json.loads(profile.friends)

        if profile.user_id == call.from_user.id:
            profile_friends_list.append(second_id)
        else:
            profile_friends_list.append(call.from_user.id)

        profile_friends_list = list(set(profile_friends_list))
        profile.friends = str(profile_friends_list)


    await call.message.edit_text(
        text=user_text.FRIEND_RESPONSE_TRUE
    )

    with suppress(*SEND_EXCEPTIONS):
        await bot.send_message(
            chat_id=second_id,
            text=user_text.FRIEND_RESPONSE_TRUE
        )


async def dialogue_request(call: CallbackQuery, bot: Bot):
    friend_id = int(call.data.split(":")[1])

    with suppress(*SEND_EXCEPTIONS):
        await bot.send_message(
            chat_id=friend_id,
            text=user_text.DIALOGUE_REQUEST_SECOND,
            reply_markup=user_kb.inline.user_request(
                request_type="dialogue_response",
                user_id=call.from_user.id
            )
        )

    await call.message.edit_caption(
        caption=user_text.DIALOGUE_REQUEST_FIRST,
        reply_markup=user_kb.inline.back_to_friends_menu()
    )


async def dialogue_response(
        call: CallbackQuery,
        bot: Bot,
        session: AsyncSession,
        dp: Dispatcher
    ):
    answer, friend_id = call.data.split(":")[1:]
    friend_id = int(friend_id)

    if answer == "false":
        await call.message.edit_text(
            text=user_text.DIALOGUE_RESPONSE_FALSE
        )

        with suppress(*SEND_EXCEPTIONS):
            return await bot.send_message(
                chat_id=friend_id,
                text=user_text.DIALOGUE_RESPONSE_FALSE
            )

    await call.message.delete()
    await create_dialogue(bot, session, dp, call.from_user.id, friend_id)


def register(router: Router):
    router.message.register(already_search_dialogue, F.text == buttons.FIND_CHAT, InQueueFilter())
    router.message.register(random_normal, F.text == buttons.FIND_CHAT)
    router.message.register(next, Command('next'))
    router.message.register(finish_dialogue, Command('stop'))
    router.message.register(finish_dialogue, F.text == buttons.STOP_DIALOG, InDialogueFilter())

    router.callback_query.register(next, F.data == "next")
    router.callback_query.register(send_feedback, F.data.startswith("send_feedback:"))
    router.callback_query.register(report, F.data.startswith("report:"))
    router.callback_query.register(previous, F.data.startswith("previous:"))
    router.message.register(male_normal, F.text == buttons.TARGET_MAN, InDialogueFilter())
    router.message.register(female_normal, F.text == buttons.TARGET_WOMAN, InDialogueFilter())

    router.message.register(friend_request, F.text == buttons.ADD_FRIEND, InDialogueFilter())
    router.callback_query.register(friend_response, F.data.startswith("friend_request:"))

    router.callback_query.register(dialogue_request, F.data.startswith("dialogue_request:"), ~ InDialogueFilter())
    router.callback_query.register(dialogue_response, F.data.startswith("dialogue_response:"), ~ InDialogueFilter())

    router.message.register(message_copy_to, InDialogueFilter())
