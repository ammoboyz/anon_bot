import os

from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date

from .. import Base
from ..base import bigint


class Captcha(Base):
    __tablename__ = "captcha"
    __table_args__ = {'schema': 'users'}

    user_id: Mapped[bigint] = mapped_column(primary_key=True, autoincrement=True)
    done: Mapped[bool] = mapped_column(default=False)
    where_from: Mapped[str] = mapped_column(default="")
    reg_date: Mapped[date] = mapped_column(default=date.today)
