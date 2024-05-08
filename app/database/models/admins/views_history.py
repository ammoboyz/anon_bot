import os
from datetime import date as dt

from sqlalchemy.orm import Mapped, mapped_column

from .. import Base
from ..base import bigint


class ViewsHistory(Base):
    __tablename__ = "shows_history"
    __table_args__ = {'schema': 'admins'}

    id: Mapped[bigint] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[bigint] = mapped_column(default=0)
    sponsor_id: Mapped[bigint] = mapped_column(default=0)
    date: Mapped[dt] = mapped_column(default=dt.today)
