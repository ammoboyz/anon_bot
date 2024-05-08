from aiogram.types import BotCommand


START_COMMANDS = [
    BotCommand(
        command="/start", # 1
        description="▶️ Открыть меню"
    ),
    BotCommand(
        command="/chat", # 1
        description="💬 Добавить в чат"
    ),
    BotCommand(
        command="/search",
        description="⚙️ Настроить поиск"
    ),
    BotCommand(
        command="/prem", # 1
        description="💎 PREMIUM"
    ),
    BotCommand(
        command="/top", # 1
        description="🏆 ТОП"
    ),
    BotCommand(
        command="/ref", # 1
        description="🌟 Рефералы"
    ),
    BotCommand(
        command="/bro", # 1
        description="🙏 Друзья"
    ),
    BotCommand(
        command="/profile", # 1
        description="🧢 Анкета"
    )
]
