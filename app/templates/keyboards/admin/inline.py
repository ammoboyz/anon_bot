from typing import List

from aiogram import Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_widgets.pagination import KeyboardPaginator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.models import Advertising, Sponsors, Shows
from app.utils import kb_wrapper


def admin_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    button_list = [
        ("✉️ Рассылка", "mailling"),
        ("💸 Партнёрство", "sponsors_menu"),
        ("⛓ Ссылки", "link_menu"),
        ("📊 Статистика", "stat_7"),
        ("📃 Скачать БД", "download_db"),
        ("🔄 Рестарт", "restart"),
        #("♿️ Удалить неактив", "delete_inactive"),
    ]

    for button in button_list:
        builder.add(
            InlineKeyboardButton(
                text=button[0],
                callback_data=button[1]
            )
        )

    builder.adjust(2)
    return builder.as_markup()


def ads() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text = '🆕 Добавить',
            callback_data= 'link_add'
        ),
        InlineKeyboardButton(
            text = '🚮 Удалить',
            callback_data= 'link_delete'
        )
    )
    builder.row(
        InlineKeyboardButton(
            text = '◀️ Назад',
            callback_data= 'admin_menu'
        )
    )
    return builder.as_markup()


def go_back(section = 'admin_menu') -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text='◀️ Назад',
            callback_data=section
        )
    )

    return builder.as_markup()


def sure_delete_link(token: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="🚮 Да, удалить",
            callback_data=f"delete_{token}"
        ),
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=f"linkstat_{token}_7"
        )
    )

    return builder.as_markup()


def link_manage(token: str, interval: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if interval <= 5:
        callback_minus = "pass"
    else:
        callback_minus = f"linkstat_{token}_{interval - 1}"

    if interval >= 20:
        callback_plus = "pass"
    else:
        callback_plus = f"linkstat_{token}_{interval + 1}"

    builder.row(
        InlineKeyboardButton(
            text="➖",
            callback_data=callback_minus
        ),
        InlineKeyboardButton(
            text=f"{interval} дней",
            callback_data="pass"
        ),
        InlineKeyboardButton(
            text=f"➕",
            callback_data=callback_plus
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="🚮 Удалить",
            callback_data=f"sure_delete_{token}"
        ),
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="link_menu"
        )
    )

    return builder.as_markup()


def link_menu(ads_list: List[Advertising], router_admin: Router) -> InlineKeyboardMarkup:
    additional_buttons = [
        [
            InlineKeyboardButton(
                text = '🆕 Добавить',
                callback_data= 'link_add'
            ),
            InlineKeyboardButton(
                text = '◀️ Назад',
                callback_data= 'admin_menu'
            )
        ]
    ]

    ref_button_list = []
    i = 0
    for ref_element in ads_list:
        i += 1

        ref_button_list.append(
            InlineKeyboardButton(
                text=f"{i}) {ref_element.name} - {ref_element.count} 👥",
                callback_data=f"linkstat_{ref_element.token}_7"
            )
        )

    return KeyboardPaginator(
        data=ref_button_list,
        additional_buttons=additional_buttons,
        router=router_admin,
    ).as_markup()


def stats(interval: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if interval <= 5:
        callback_minus = "pass"
    else:
        callback_minus = f"stat_{interval - 1}"

    if interval >= 20:
        callback_plus = "pass"
    else:
        callback_plus = f"stat_{interval+1}"

    builder.row(
        InlineKeyboardButton(
            text="➖",
            callback_data=callback_minus
        ),
        InlineKeyboardButton(
            text=f"{interval} дней",
            callback_data="pass"
        ),
        InlineKeyboardButton(
            text=f"➕",
            callback_data=callback_plus
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="admin_menu"
        )
    )

    return builder.as_markup()


def admin_back() -> InlineKeyboardMarkup:
    keyboard_list = []
    keyboard_list.append([InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="admin_menu"
    )])
    return InlineKeyboardMarkup(
        inline_keyboard=keyboard_list
    )


def stop_mailling() -> InlineKeyboardMarkup:
    keyboard_list = []
    keyboard_list.append([InlineKeyboardButton(
        text="⛔️ Cтоп-кран",
        callback_data="stop_mailling"
    )])
    return InlineKeyboardMarkup(
        inline_keyboard=keyboard_list
    )


def delete_message() -> InlineKeyboardMarkup:
    keyboard_list = []
    keyboard_list.append([InlineKeyboardButton(
        text="🗑 Удалить",
        callback_data="delete"
    )])
    return InlineKeyboardMarkup(
        inline_keyboard=keyboard_list
    )


def mailling_approve() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text="Да",
        callback_data="mailling_start"
    )

    builder.button(
        text="Нет",
        callback_data="admin_menu"
    )

    return builder.as_markup()


def sponsor_choose(sponsor_type: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text="👥 Канал",
        callback_data="add_channel"
    )

    builder.button(
        text="🤖 Робот",
        callback_data="add_bot"
    )

    builder.button(
        text="◀️ Назад",
        callback_data=f"sponsors_list:{sponsor_type}"
    )

    builder.adjust(2, 1)
    return builder.as_markup()


async def sponsors_list(
    session: AsyncSession,
    router: Router,
    sponsor_type: str
) -> InlineKeyboardMarkup:
    data_builder = InlineKeyboardBuilder()

    add_buttons = [
        [
            InlineKeyboardButton(
                text="🆕 Добавить",
                callback_data=f"add_sponsor:{sponsor_type}"
            ),
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="sponsors_menu"
            )
        ]
    ]

    sponsors_list = (await session.scalars(
        select(Sponsors)
        .order_by(Sponsors.create_date)
    )).all()

    i = 0
    for sponsor in sponsors_list:
        i += 1

        if sponsor.is_show and sponsor_type == "show":
            show = await session.scalar(
                select(Shows)
                .where(Shows.id == sponsor.id)
            )

            add_text = " (привет)" if show.is_hello else " (обычный)"

            data_builder.button(
                text=f"{i}) " + (sponsor.first_name) + add_text,
                callback_data=f"manage_sponsor:{sponsor_type}:{sponsor.id}"
            )

        elif not sponsor.is_show and sponsor_type == "op":
            data_builder.button(
                text=f"{i}) " + sponsor.first_name,
                callback_data=f"manage_sponsor:{sponsor_type}:{sponsor.id}"
            )

    return KeyboardPaginator(
        data=data_builder.buttons,
        router=router,
        additional_buttons=add_buttons,
        per_row=1
    ).as_markup()


def sponsor_manage(sponsor_id: int, sponsor_type: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text="🚮 Удалить",
        callback_data=f"sponsor_approve:{sponsor_type}:{sponsor_id}"
    )

    builder.button(
        text="◀️ Назад",
        callback_data=f"sponsors_list:{sponsor_type}"
    )

    builder.adjust(2)
    return builder.as_markup()


def sponsor_approve_delete(sponsor_id: int, sponsor_type: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Удалить",
        callback_data=f"sponsor_delete:{sponsor_type}:{sponsor_id}"
    )

    builder.button(
        text="◀️ Назад",
        callback_data=f"sponsors_list:{sponsor_type}"
    )

    builder.adjust(2)
    return builder.as_markup()


@kb_wrapper
def show_type(builder: InlineKeyboardBuilder) -> InlineKeyboardMarkup:
    builder.button(
        text="👋 Привет",
        callback_data="show_type:hello"
    )

    builder.button(
        text="👌 Обычный",
        callback_data="show_type:default"
    )

    builder.button(
        text="◀️ Назад",
        callback_data="sponsors_menu"
    )

    builder.adjust(2, 1)


@kb_wrapper
def sponsors_type(builder: InlineKeyboardBuilder) -> InlineKeyboardMarkup:
    builder.button(
        text="✍️ ОП",
        callback_data="sponsors_list:op"
    )

    builder.button(
        text="📣 Показы",
        callback_data="sponsors_list:show"
    )

    builder.button(
        text = "◀️ Назад",
        callback_data= "admin_menu"
    )

    builder.adjust(2, 1)
