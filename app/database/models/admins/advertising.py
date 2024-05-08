import os

from .. import Base
from ..base import bigint

from datetime import datetime as dt
from sqlalchemy.orm import Mapped, mapped_column


class Advertising(Base):
    __tablename__ = "ads"
    __table_args__ = {'schema': 'admins'}

    token: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    count: Mapped[int] = mapped_column(default=0)

    date: Mapped[dt] = mapped_column(default=dt.today)
