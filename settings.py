import os

from aiogram.exceptions import (
    TelegramForbiddenError,
    TelegramBadRequest,
    TelegramAPIError
)


DB_NANE: str = os.getenv('DB_NAME')
MERCHANT_ID: str = os.getenv('MERCHANT_ID')
SECRET_KEY: str = os.getenv('SECRET_KEY')
BOT_TOKEN: str = os.getenv('BOT_TOKEN')


VIP_OPTIONS = {
    'day': {
        'msg_name': 'подписка на 1 день',
        'call_name': ' 1 день - {}р',
        'method_name': 'premium',
        'amount': 69,
        'days': 1,
        'show_in_menu': True
    },
    'week': {
        'msg_name': 'подписка на 7 дней',
        'call_name': '🔥 7 дней - {}р',
        'method_name': 'premium',
        'amount': 199,
        'days': 7,
        'show_in_menu': True
    },
    'month': {
        'msg_name': 'подписка на месяц',
        'call_name': '30 дней - {}р',
        'method_name': 'premium',
        'amount': 249,
        'days': 30,
        'show_in_menu': True
    },
    'forever': {
        'msg_name': 'подписка навсегда',
        'call_name': 'Навсегда - {}р',
        'method_name': 'premium',
        'amount': 499,
        'days': 2000,
        'show_in_menu': True
    },
    'roulette': {
        'msg_name': 'рулетка',
        'call_name': '🎰 Рулетка | НОВОЕ 🔥',
        'method_name': 'roulette',
        'amount': 149,
        'show_in_menu': True
    },
    'nullable_rate': {
        'msg_name': 'обнуление рейтинга',
        'call_name': 'Обнуление рейтинга - 50р',
        'method_name': 'nullable_rate',
        'amount': 50,
        'show_in_menu': False
    }
}


SEND_EXCEPTIONS = [
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError
]


with open('./app/utils/ban_words.txt', 'r', encoding='utf-8') as file:
    BAN_WORDS = file.read().split("\n")
