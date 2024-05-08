import json
import random
from typing import Optional, Any

from aiogram import Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_widgets.pagination import KeyboardPaginator

from settings import VIP_OPTIONS
from app.utils import (
    kb_wrapper,
    InterestsCallbackFactory,
    PremiumCallbackFactory,
    func
)


def builder_cycle(
        builder: InlineKeyboardBuilder,
        button_list: list[tuple[str, str]]
    ) -> InlineKeyboardBuilder:
    for text, callback_data in button_list:
        builder.button(
            text=text,
            callback_data=callback_data
        )

    return builder


@kb_wrapper
def captcha(builder: InlineKeyboardBuilder) -> InlineKeyboardMarkup:
    button_list = [
        ("Я М 🧑🏻", "choise_sex_none_reg:man"),
        ("Я Д 👩🏼", "choise_sex_none_reg:woman")
    ]

    builder = builder_cycle(builder, button_list)

    builder.adjust(2)


@kb_wrapper
def change_gender(
        builder: InlineKeyboardBuilder,
        action_type: str = "choise_sex"
    ) -> InlineKeyboardMarkup:
    button_list = [
        ("Я М 🧑🏻", f"{action_type}:man"),
        ("Я Д 👩🏼", f"{action_type}:woman")
    ]

    builder = builder_cycle(builder, button_list)

    builder.adjust(2)


@kb_wrapper
def profile(builder: InlineKeyboardBuilder) -> InlineKeyboardMarkup:
    builder.button(
        text="👻 Профиль",
        callback_data="profile_user"
    )

    builder.button(
        text="💈 Статистика",
        callback_data="profile_stats"
    )

    builder.adjust(2)


@kb_wrapper
def profile_user(builder: InlineKeyboardBuilder) -> InlineKeyboardMarkup:
    button_list = [
        ("Изменить пол", "profile_change:gender"),
        ("Изменить возраст", "profile_change:age"),
        ("Изменить интересы", "profile_change:interests"),
        ("🤩 Обнулить рейтинг", "profile_change:nullable_rate"),
        ("◀️ Назад", "profile")
    ]

    builder_cycle(builder, button_list)

    builder.adjust(2, 1, 1, 1)


@kb_wrapper
def back_to_profile(builder: InlineKeyboardBuilder) -> InlineKeyboardMarkup:
    builder.button(
        text="◀️ Назад в профиль",
        callback_data="profile"
    )


@kb_wrapper
def choose_sex_none_reg(builder: InlineKeyboardBuilder) -> InlineKeyboardMarkup:
    button_list = [
        ("Я М 🧑🏻", "choise_sex_none_reg:man"),
        ("Я Д 👩🏼", "choise_sex_none_reg:woman")
    ]

    builder = builder_cycle(builder, button_list)
    builder.adjust(2)


@kb_wrapper
def premium_list(
    builder: InlineKeyboardBuilder,
    discount: int = 0
) -> InlineKeyboardMarkup:
    for key, value in VIP_OPTIONS.items():
        if not value.get('show_in_menu'):
            continue

        if value.get('method_name') != "premium":
            continue

        builder.button(
            text=value.get('call_name').format(func.subtract_discount(value.get('amount'), discount)) + (
                f" (вместо {value.get('amount')}р)"
                if func.subtract_discount(value.get('amount'), discount) != value.get('amount')
                else ""
            ),
            callback_data=PremiumCallbackFactory(
                amount=func.subtract_discount(value.get('amount'), discount),
                product=key,
                callback_back="premium_list"
            )
        )

    if discount == 0:
        builder.button(
            text="◀️ Назад",
            callback_data="premium"
        )

    builder.adjust(1)


@kb_wrapper
def premium(builder: InlineKeyboardBuilder) -> InlineKeyboardMarkup:
    builder.button(
        text="💎 Купить премиум",
        callback_data="premium_list"
    )

    builder.button(
        text=VIP_OPTIONS.get('roulette').get('call_name'),
        callback_data=PremiumCallbackFactory(
            product='roulette',
            amount=VIP_OPTIONS.get('roulette').get('amount'),
            callback_back="premium"
        )
    )

    builder.button(
        text="🏆 Получить бесплатно",
        callback_data="premium_free"
    )

    builder.adjust(1)


@kb_wrapper
def payment_create(
        builder: InlineKeyboardBuilder,
        callback_back: str,
        payment_url: str
    ) -> InlineKeyboardMarkup:
    builder.button(
        text="Выбрать способ оплаты 💸",
        url=payment_url
    ),
    builder.button(
        text="◀️ Назад",
        callback_data=callback_back
    )

    builder.adjust(1)


@kb_wrapper
def change_age(
        builder: InlineKeyboardBuilder,
        action_type: str = "add_age"
    ) -> InlineKeyboardMarkup:
    for i in range(8, 23):
        builder.button(
            text=f"{i}{'+' if i == 22 else ''}",
            callback_data=f"{action_type}:{i}"
        )

    builder.adjust(5)


@kb_wrapper
def send_feedback(
        builder: InlineKeyboardBuilder,
        user_id: int,
        feedback_sended: bool = False
    ) -> InlineKeyboardMarkup:
    feedback_buttons = {
        "🔥": f"send_feedback:fire:{user_id}",
        "😈": f"send_feedback:satan:{user_id}",
        "🤡": f"send_feedback:clown:{user_id}",
        "💩": f"send_feedback:shit:{user_id}",
        "◀️ Предыдущий": f"previous:{user_id}",
        "Следующий ▶️": "next",
        "👮🏻‍♂️ Пожаловаться (спам/реклама)": f"report:{user_id}"
    }

    for text, callback_data in feedback_buttons.items():
        if callback_data.startswith("send_feedback") and feedback_sended:
            continue

        builder.button(
            text=text,
            callback_data=callback_data
        )

    if feedback_sended:
        builder.adjust(2, 1)
    else:
        builder.adjust(4, 2, 1)


def friends_menu(friends_dict: dict[int, str], router: Router) -> InlineKeyboardMarkup:
    buttons_data = []

    for user_id, first_name in friends_dict.items():
        buttons_data.append(
            InlineKeyboardButton(
                text=first_name,
                callback_data=f"friend:{user_id}"
            )
        )

    return KeyboardPaginator(
        data=buttons_data,
        router=router,
        per_page=2,
        per_row=5
    ).as_markup()


@kb_wrapper
def friend(builder: InlineKeyboardBuilder, friend_id: int) -> InlineKeyboardMarkup:
    builder.button(
        text="📩 Диалог",
        callback_data=f"dialogue_request:{friend_id}"
    )

    builder.button(
        text="💔 Удалить",
        callback_data=f"friend_delete:{friend_id}"
    )

    builder.button(
        text="◀️ Назад",
        callback_data="friends_menu"
    )

    builder.adjust(2, 1)


@kb_wrapper
def back_to_friends_menu(builder: InlineKeyboardBuilder) -> InlineKeyboardMarkup:
    builder.button(
        text="◀️ Назад",
        callback_data="friends_menu"
    )


@kb_wrapper
def user_request(builder: InlineKeyboardBuilder, request_type: str, user_id: int) -> InlineKeyboardMarkup:
    builder.button(
        text="✅ Принять",
        callback_data=f"{request_type}:true:{user_id}"
    )

    builder.button(
        text="❌ Отклонить",
        callback_data=f"{request_type}:false:{user_id}"
    )

    builder.adjust(2)


@kb_wrapper
def change_interests(
    builder: InlineKeyboardBuilder,
    already_interests: list[str],
    callback_data: InterestsCallbackFactory = None,
) -> InlineKeyboardMarkup:
    interests_list = [
        "Спорт",
        "Музыка",
        "Книги",
        "Творчество",
        "Тусовки",
        "Игры",
        "Учёба",
        "Блогинг",
        "Аниме",
        "Сериалы",
        "TikTok",
        "Животные"
    ]

    for interest in interests_list:
        finish_text = interest
        active = False

        if callback_data:
            if  (
                    callback_data.is_active or
                    callback_data.interest == interest or
                    interest in already_interests
                ):
                finish_text = "✅ " + interest
                active = True

        builder.button(
            text=finish_text,
            callback_data=InterestsCallbackFactory(
                action="change_interests",
                interest=interest,
                is_active=active
            )
        )

    builder.button(
        text="Ничем не интересуюсь 🥹",
        callback_data="profile_interests:None"
    )

    builder.button(
        text="◀️ Назад",
        callback_data="profile"
    )

    builder.adjust(3, 3, 3, 3, 1, 1)


@kb_wrapper
def nullable_rate(builder: InlineKeyboardBuilder) -> InlineKeyboardMarkup:
    builder.button(
        text="Оплатить 🔥 50 руб",
        callback_data=PremiumCallbackFactory(
            amount=50,
            product="nullable_rate",
            callback_back="profile"
        )
    )

    builder.button(
        text="◀️ Назад",
        callback_data="profile"
    )

    builder.adjust(1)


@kb_wrapper
def top(builder: InlineKeyboardBuilder):
    builder.button(
        text="Получить бесплатный 💎 PREMIUM",
        callback_data="premium_free:skip_back"
    )


@kb_wrapper
def profile_stats(builder: InlineKeyboardBuilder):
    builder.button(
        text="◀️ Назад",
        callback_data="profile"
    )


@kb_wrapper
def premium_free(
    builder: InlineKeyboardBuilder,
    bot_username: str,
    user_id: int,
    skip_back: bool = False
):
    builder.button(
        text="👉 Поделиться ссылкой",
        url=f"http://t.me/share/url?url=t.me/{bot_username}?start=r{user_id}&text=%0A%D0%91%D0%BE%D1%82%20%D0%B4%D0%BB%D1%8F%20%D0%B0%D0%BD%D0%BE%D0%BD%D0%B8%D0%BC%D0%BD%D0%BE%D0%B3%D0%BE%20%D0%BE%D0%B1%D1%89%D0%B5%D0%BD%D0%B8%D1%8F%20%D0%B2%20Telegram%20%F0%9F%92%99%0A%D0%9F%D0%BE%D0%B8%D1%81%D0%BA%20%D0%BF%D0%BE%20%D0%BF%D0%BE%D0%BB%D1%83%20%D0%B8%20%D0%B2%D0%BE%D0%B7%D1%80%D0%B0%D1%81%D1%82%D1%83%2C%20%D0%BA%D0%BE%D0%BC%D0%BD%D0%B0%D1%82%D1%8B%20%D0%BF%D0%BE%20%D0%B8%D0%BD%D1%82%D0%B5%D1%80%D0%B5%D1%81%D0%B0%D0%BC%20%F0%9F%98%BB%0A%0A%D0%A1%D0%BA%D0%BE%D1%80%D0%B5%D0%B5%20%D1%80%D0%B5%D0%B3%D0%B8%D1%81%D1%82%D1%80%D0%B8%D1%80%D1%83%D0%B9%D1%81%D1%8F%20%D0%BF%D0%BE%20%D0%BC%D0%BE%D0%B5%D0%B9%20%D1%81%D1%81%D1%8B%D0%BB%D0%BA%D0%B5%2C%20%D1%87%D1%82%D0%BE%D0%B1%D1%8B%20%D0%BF%D0%BE%D0%BB%D1%83%D1%87%D0%B8%D1%82%D1%8C%20%D0%B1%D0%B5%D1%81%D0%BF%D0%BB%D0%B0%D1%82%D0%BD%D1%8B%D0%B9%20%F0%9F%92%8E%20PREMIUM"
    )

    if not skip_back:
        builder.button(
            text="◀️ Назад",
            callback_data="premium"
        )

    builder.adjust(1)


@kb_wrapper
def change_search(builder: InlineKeyboardBuilder) -> InlineKeyboardMarkup:
    builder.button(
        text="🍌 Пол",
        callback_data="change_search:gender"
    )

    builder.button(
        text="🧨 Возраст",
        callback_data="change_search:age"
    )

    builder.button(
        text="🚪 Комната",
        callback_data="change_search:room"
    )

    builder.adjust(2, 1)


def create_choose_button(
        builder: InlineKeyboardBuilder,
        text: str,
        data: str,
        target: Any,
        match: Any
) -> None:
    if target == match:
        text = f"✅ {text}"
        data = "pass"

    builder.button(text=text, callback_data=data)


@kb_wrapper
def change_search_gender(
    builder: InlineKeyboardBuilder,
    target_man: Optional[bool] = None
) -> InlineKeyboardMarkup:
    gender_list = [
        ("М 🧑🏻", "change_search:gender:man", True),
        ("Д 👩🏼", "change_search:gender:woman", False),
        ("Любой", "change_search:gender:any", None)
    ]

    for text, data, checked in gender_list:
        create_choose_button(builder, text, data, target_man, checked)

    builder.button(text="◀️ Назад", callback_data="change_search")
    builder.adjust(2, 1, 1)


@kb_wrapper
def change_search_age(
    builder: InlineKeyboardBuilder,
    target_age: list = []
) -> InlineKeyboardMarkup:
    age_list = [
        ("8-10", "change_search:age:[8, 9, 10]", [8, 9, 10]),
        ("11-13", "change_search:age:[11, 12, 13]", [11, 12, 13]),
        ("14-16", "change_search:age:[14, 15, 16]", [14, 15, 16]),
        ("17-19", "change_search:age:[17, 18, 19]", [17, 18, 19]),
        ("20-22", "change_search:age:[20, 21, 22]", [20, 21, 22]),
        ("22+", "change_search:age:[22, 23, 24]", [22, 23, 24]),
        ("Любой", "change_search:age:[]", [])
    ]

    for text, data, checked in age_list:
        create_choose_button(builder, text, data, target_age, checked)

    builder.button(
        text="◀️ Назад",
        callback_data="change_search"
    )

    builder.adjust(3, 3, 1, 1)


@kb_wrapper
def change_search_room(
    builder: InlineKeyboardBuilder,
    target_room: str = ""
):
    room_categories = [
        "Общение",
        "Флирт",
        "Обмен фото",
        "Голосовые",
        "Фильмы",
        "Аниме",
        "Общая"
    ]

    room_list = []

    for category in room_categories:
        room_list.append(
            (
                category,
                f"change_search:room:{category}"
            )
        )

    for text, data in room_list:
        create_choose_button(builder, text, data, text, target_room)

    builder.button(
        text="◀️ Назад",
        callback_data="change_search"
    )

    builder.adjust(3, 3, 1, 1)


@kb_wrapper
def offer_premium(builder: InlineKeyboardBuilder) -> InlineKeyboardMarkup:
    builder.button(
        text="Преимущества 💎 PREMIUM",
        callback_data="premium"
    )


@kb_wrapper
def casino(builder: InlineKeyboardBuilder) -> InlineKeyboardMarkup:
    builder.button(
        text="Прокрутить рулетку! 🎰",
        callback_data="casino"
    )


@kb_wrapper
def game(builder: InlineKeyboardBuilder, user_id: int) -> InlineKeyboardMarkup:
    result_list = [0, 0, 1]
    random.shuffle(result_list)

    for result in result_list:
        builder.button(
            text="🥚",
            callback_data=f"game:{user_id}:{result}"
        )


@kb_wrapper
def start_chat(
    builder: InlineKeyboardBuilder,
    bot_username: str,
    text: str = "👉 Добавить в свой чат (группу)"
) -> InlineKeyboardMarkup:
    builder.button(
        text=text,
        url=f"https://t.me/{bot_username}?startgroup=true"
    )


@kb_wrapper
def report(builder: InlineKeyboardBuilder, user_id: int) -> InlineKeyboardMarkup:
    builder.button(
        text="Забанить",
        callback_data=f"ban:{user_id}"
    )
