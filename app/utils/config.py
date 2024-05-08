import json

from pydantic_settings import BaseSettings


class DB(BaseSettings):
    host: str
    port: int
    name: str
    user: str
    password: str


class Payments(BaseSettings):
    api_key: str


class Bot(BaseSettings):
    timezone: str
    manager_link: str
    admins: list[int]
    admin_chat: int
    backup_chat: int
    report_chat: int


class Settings(BaseSettings):
    bot: Bot
    db: DB
    payments: Payments

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"


def load_config(env_file=".env") -> Settings:
    """
    Loads .env file into BaseSettings

    :param str env_file: Env file, defaults to ".env"
    :return Settings: Settings object
    """

    settings = Settings(_env_file=env_file)
    return settings
