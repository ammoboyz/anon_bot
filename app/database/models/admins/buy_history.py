import os

from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column

from .. import Base
from ..base import bigint


class BuyHistory(Base):
    __tablename__ = "buy_history"
    __table_args__ = {'schema': 'admins'}

    pay_code: Mapped[str] = mapped_column(primary_key=True)

    user_id: Mapped[bigint] = mapped_column(default=0)
    amount: Mapped[int] = mapped_column(default=0)
    buy_date: Mapped[datetime] = mapped_column(default=datetime.now)
    where_from: Mapped[str] = mapped_column(default="")
