import os

from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column

from .. import Base
from ..base import bigint


class Sponsors(Base):
    __tablename__ = "sponsors"
    __table_args__ = {'schema': 'admins'}

    id: Mapped[bigint] = mapped_column(primary_key=True, autoincrement=True)

    is_show: Mapped[bool] = mapped_column(default=False)
    first_name: Mapped[str] = mapped_column(default="")
    url: Mapped[str] = mapped_column(default="")
    is_bot: Mapped[bool] = mapped_column(default=False)
    token: Mapped[str] = mapped_column(default="")

    create_date: Mapped[datetime] = mapped_column(default=datetime.now)
    count: Mapped[int] = mapped_column(default=0)
