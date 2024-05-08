import datetime
import io, os
import matplotlib.pyplot as plt
from contextlib import suppress

from aiogram import Bot
from aiogram.types import FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from settings import SEND_EXCEPTIONS
from app.database.models import (
    Users, Sponsors, Shows, ViewsHistory, Captcha, Chats, BuyHistory
)


class StatisticsPlotter:
    """A class to generate and plot statistics based on registration, blockage.

    Args:
        interval (int): The number of days for the interval.
        date_reg (list): List of dates for registrations.
        date_dead (list): List of dates for blockages.
        label_reg (str, optional): Label for registration data. Defaults to "Registration".
        label_dead (str, optional): Label for blockage data. Defaults to "Blockage".

    Methods:
        generate_data: Generates data based on the provided intervals and dates.
        plot_statistics: Plots statistics for the given data and returns an image buffer in BytesIO format.
    """

    def __init__(
            self,
            interval: int,
            session: AsyncSession,
            date_reg: list = [],
            ads_token: str = "",
            label_reg: str = "Воспользовались ботом",
            label_dead: str = "Умерло"):

        self.session = session
        self.ads_token = ads_token

        self.today = datetime.date.today()
        self.interval = interval

        self.date_reg = date_reg
        self.date_dead = [datetime.date.today()]

        self.label_reg = label_reg
        self.label_dead = label_dead


    @staticmethod
    def formatted_integer(integer: int) -> str:
        if integer < 1000:
            return str(integer)

        prefix = ""

        while integer >= 1000:
            integer //= 1000
            prefix = prefix + "к"

        result = f"{integer}{prefix}"
        return result


    def generate_data(self):
        data = []

        for i in range(self.interval - 1, -1, -1):
            count_reg = self.date_reg.count(self.today - datetime.timedelta(days=i))
            count_dead = self.date_dead.count(self.today - datetime.timedelta(days=i))

            data.append((count_reg, count_dead))

        end_date = self.today
        date_list = [end_date - datetime.timedelta(days=i) for i in range(self.interval - 1, -1, -1)]
        days = [date.strftime("%d.%m.%Y") for date in date_list]

        return data, days


    async def get_records(self) -> None:
        stmt = select(Users)
        if self.ads_token:
            stmt = stmt.where(Users.where_from == self.ads_token)

        users_list = (await self.session.scalars(stmt)).all()

        self.date_dead = [date_element.dead_date for date_element in users_list]
        self.date_reg = [date_element.reg_date for date_element in users_list]


    async def plot_statistics(self) -> io.BytesIO:
        await self.get_records()

        data, days = self.generate_data()

        fig, ax = plt.subplots(figsize=(12, 6))

        ax.set_title(f"Статистика за последние {self.interval} дней")
        ax.set_xlabel("Дни")
        ax.set_ylabel("Количество")

        registration = [day[0] for day in data]
        deaths = [day[1] for day in data]

        bar_width = 0.4
        step = 0.2

        ax.bar([i - step for i in range(len(days))], registration, width=bar_width, label=self.label_reg, color="blue")
        ax.bar([i + step for i in range(len(days))], deaths, width=bar_width, label=self.label_dead, color="red")

        ax.set_xticks(range(len(days)))
        ax.set_xticklabels(days)
        plt.xticks(rotation=45, fontsize=8)
        ax.legend()

        reqs_empty = registration.count(0) == self.interval
        deads_empty = deaths.count(0) == self.interval

        if not (reqs_empty and deads_empty):
            for i, v in enumerate(registration):
                ax.text(i - step, v + 0.005, self.formatted_integer(v), ha='center', va='bottom')
            for i, v in enumerate(deaths):
                ax.text(i + step, v + 0.005, self.formatted_integer(v), ha='center', va='bottom')

        buff = io.BytesIO()
        plt.savefig(buff, format="png")

        plt.close()

        return buff


    def shows_plot_statistic(self) -> io.BytesIO:
        data, days = self.generate_data()

        fig, ax = plt.subplots(figsize=(12, 6))

        ax.set_title(f"Статистика за последние {self.interval} дней")
        ax.set_xlabel("Дни")
        ax.set_ylabel("Количество")

        registration = [day[0] for day in data]

        bar_width = 0.4

        ax.bar([i for i in range(len(days))], registration, width=bar_width, label=self.label_reg, color="blue")

        ax.set_xticks(range(len(days)))
        ax.set_xticklabels(days)
        plt.xticks(rotation=45, fontsize=8)
        ax.legend()

        reqs_empty = registration.count(0) == self.interval

        if not reqs_empty:
            for i, v in enumerate(registration):
                ax.text(i, v + 0.005, self.formatted_integer(v), ha='center', va='bottom')

        buff = io.BytesIO()
        plt.savefig(buff, format="png")

        plt.close()

        return buff


class StatisticString:
    def __init__(
        self,
        session: AsyncSession,
        bot_username: str = "",
        ads_token: str = ""
    ):
        self.today = datetime.date.today()

        self.session = session
        self.ads_token = ads_token
        self.bot_username = bot_username


    async def fetch_data(self) -> None:
        users_stmt = select(Users)
        captcha_stmt = select(Captcha)
        chats_stmt = select(Chats)
        donate_stmt = select(BuyHistory)
        age_stmt = select(Users.age)
        gender_stmt = select(Users.is_man)
        chats_stmt = select(Chats)

        if self.ads_token:
            users_condition = Users.where_from == self.ads_token
            users_stmt = users_stmt.where(users_condition)
            age_stmt = age_stmt.where(users_condition)
            gender_stmt = gender_stmt.where(users_condition)

            captcha_stmt = captcha_stmt.where(Captcha.where_from == self.ads_token)
            donate_stmt = donate_stmt.where(BuyHistory.where_from == self.ads_token)

        self.users_list = (await self.session.scalars(users_stmt)).all()
        self.captcha_list = (await self.session.scalars(captcha_stmt)).all()
        self.chat_list = (await self.session.scalars(chats_stmt)).all()
        self.age_list = (await self.session.scalars(age_stmt)).all()
        self.gender_list = (await self.session.scalars(gender_stmt)).all()
        self.donate_list = (await self.session.scalars(donate_stmt)).all()
        self.chats_list = (await self.session.scalars(chats_stmt)).all()


    async def calculate_statistics(self) -> None:
        await self.fetch_data()

        self.total_users = len(self.users_list)
        self.total_captchas = len(self.captcha_list)
        self.total_chats = len(self.chats_list)
        self.total_dead = sum(1 for user in self.users_list if user.dead_date is not None)
        self.total_users -= self.total_dead
        self.total_donate = sum(buy.amount for buy in self.donate_list) if self.donate_list else 0
        self.total_from_chats = sum(1 if user.from_group else 0 for user in self.users_list)

        self.registered_users = sum(1 for user in self.users_list if user.is_man is not None)
        self.subscriptions = sum(1 for user in self.users_list if user.passed_op)

        self.male_count = sum(1 for gender in self.gender_list if gender == True)
        self.female_count = sum(1 for gender in self.gender_list if gender == False)

        self.today_captchas = sum(1 for captcha in self.captcha_list if captcha.reg_date == datetime.date.today())
        self.today_users = sum(1 for user in self.users_list if user.reg_date == datetime.date.today())
        self.today_registered_users = sum(1 for user in self.users_list if user.reg_date == datetime.date.today() and (user.is_man is not None))
        self.today_subscriptions = sum(1 for user in self.users_list if user.passed_op and user.reg_date == datetime.date.today())
        self.today_dead = sum(1 for user in self.users_list if user.dead_date == datetime.date.today())
        self.today_users -= self.today_dead
        self.today_from_chats = sum(1 if user.from_group else 0 for user in self.users_list if user.reg_date == datetime.date.today())

        self.total_users_percentage = int(((self.total_users - self.total_from_chats) / self.total_captchas) * 100) if self.total_users > 0 and self.total_from_chats > 0 else 0
        self.registered_users_percentage = int((self.registered_users / self.total_captchas) * 100) if self.registered_users > 0 and self.total_captchas > 0 and self.registered_users else 0
        self.subscriptions_percentage = int((self.subscriptions / self.total_captchas) * 100) if self.subscriptions  > 0 and self.total_captchas and self.subscriptions else 0

        self.today_users_percentage = int(((self.today_users - self.today_from_chats) / self.today_captchas) * 100) if self.total_users > 0 and self.today_from_chats > 0 else 0
        self.today_registered_users_percentage = int((self.today_registered_users / self.today_captchas) * 100) if self.today_registered_users > 0 and self.today_captchas else 0
        self.today_subscriptions_percentage = int((self.today_subscriptions / self.today_captchas) * 100) if self.total_users > 0 and self.today_captchas > 0 else 0
        self.male_count_percentage = int((self.male_count / self.registered_users) * 100) if self.registered_users > 0 and self.male_count > 0 else 0
        self.female_count_percentage = int((self.female_count / self.registered_users) * 100) if self.registered_users > 0 and self.female_count > 0 else 0

        non_none_ages = [age for age in self.age_list if age is not None]
        self.average_age = int(sum(non_none_ages) / len(non_none_ages)) if len(non_none_ages) > 0 else 0

    async def all_statistics(self) -> str:
        await self.calculate_statistics()

        return f'''
📊 <b>Статистика</b>
<code>
Всего
Переходов: {self.total_captchas}
Юзеры в чатах: {self.total_from_chats}
Пользователей: {self.total_users - self.total_from_chats} ({self.total_users_percentage}%)
Подписки: {self.subscriptions} ({self.subscriptions_percentage}%)
Зарегистрированных: {self.registered_users} ({self.registered_users_percentage}%)
Мёртвых: {self.total_dead}
Чатов: {self.total_chats}
Всего покупок на сумму: {self.total_donate}р

За сегодня
Переходов: {self.today_captchas}
Юзеры в чатах: {self.today_from_chats}
Пользователей: {self.today_users - self.today_from_chats} ({self.today_users_percentage}%)
Подписки: {self.today_subscriptions} ({self.today_subscriptions_percentage}%)
Зарегистрированных: {self.today_registered_users} ({self.today_registered_users_percentage}%)
Умерло: {self.today_dead}

Средний возраст: {self.average_age} лет
{self.male_count}🧑🏻({self.male_count_percentage}%) | {self.female_count}👩🏼({self.female_count_percentage}%)
</code>
'''


    async def ads_statistics(self) -> str:
        await self.calculate_statistics()

        return f'''
📊 <b>Статистика</b>
<code>
Всего
Переходов: {self.total_captchas}
Пользователей: {self.total_users - self.total_from_chats} ({self.total_users_percentage}%)
Подписки: {self.subscriptions} ({self.subscriptions_percentage}%)
Зарегистрированных: {self.registered_users} ({self.registered_users_percentage}%)
Мёртвых: {self.total_dead}
Всего покупок на сумму: {self.total_donate}р

За сегодня
Переходов: {self.today_captchas}
Пользователей: {self.today_users} ({self.today_users_percentage}%)
Подписки: {self.today_subscriptions} ({self.today_subscriptions_percentage}%)
Зарегистрированных: {self.today_registered_users} ({self.today_registered_users_percentage}%)
Умерло: {self.today_dead}

Средний возраст: {self.average_age} лет
{self.male_count}🧑🏻({self.male_count}%) | {self.female_count}👩🏼({self.female_count}%)</code>

<b>🔗 Ссылка:</b> <code>https://t.me/{self.bot_username}?start=ads{self.ads_token}</code>
'''


async def report(text: str, list_id: list, bot: Bot) -> None:
    for user_id in list_id:
        with suppress(*SEND_EXCEPTIONS):
            await bot.send_message(
                chat_id=user_id,
                text=text
            )


def sponsor_get_info(sponsor: Sponsors) -> str:
    return f'''
<b>💸 Спонсор <code>{sponsor.first_name}</code>:</b>

<b>📊 Всего подписалось:</b> <code>{sponsor.count}</code>

<b>🆔 ID:</b> <code>{sponsor.id}</code>
<b>🔗 Ссылка:</b> <code>{sponsor.url}</code>
<b>🔎 Это:</b> <code>{"бот 🤖" if sponsor.is_bot else "канал/чат 👥"}</code>
{f"<b>👨‍💻 Токен:</b> <code>{sponsor.token}</code>" if sponsor.token else ""}
'''


async def show_get_info(session: AsyncSession, sponsor_id: int) -> tuple[str, io.BytesIO]:
    show = await session.scalar(
        select(Shows)
        .where(Shows.id == sponsor_id)
    )

    view_history = (await session.scalars(
        select(ViewsHistory)
        .where(ViewsHistory.sponsor_id == sponsor_id)
    )).all()

    show_date = (await session.scalars(
        select(ViewsHistory.date)
        .where(ViewsHistory.sponsor_id == sponsor_id)
    )).all()

    views_today = 0
    views_week = 0
    views_month = 0

    today = datetime.date.today()

    for view in view_history:
        if today == view.date:
            views_today += 1

        elif (today - view.date).days <= 7:
            views_week += 1

        elif (today - view.date).days <= 30:
            views_month += 1

    stats_pic = StatisticsPlotter(
        interval=14,
        session=session,
        date_reg=show_date,
        label_reg="Показы"
    ).shows_plot_statistic()

    finish_text = f'''
<b>💸 Спонсор <code>{show.name}</code>:</b>

<b>👥 Просмотрено всего: <code>{show.views}</code></b>

<b>📊 Просмотрено сегодня: <code>{views_today}</code></b>
<b>📊 Просмотрено вчера: <code>{views_week}</code></b>
<b>📊 Просмотрено за месяц: <code>{views_month}</code></b>

<b>❌ Лимит: <code>{show.views_limit}</code></b>
<b>ℹ️ Работает: <code>{"да" if show.is_actual else "нет"}</code></b>
'''

    return finish_text, stats_pic


def id_to_txt(list_id: list[int | str]) -> FSInputFile:
    date_now = datetime.datetime.now()
    date_now = date_now.strftime("%d-%m-%Y_%H-%M-%S")
    with open(f"app/database/{date_now}.txt", "w", encoding="utf-8") as file:
        for user_id in list_id:
            file.write(str(user_id) + "\n")

    input_file = FSInputFile(f"app/database/{date_now}.txt", f"{date_now}.txt")
    os.remove(f"app/database/{date_now}.txt")

    return input_file
