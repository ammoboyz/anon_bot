from typing import Optional

from .. import Base
from ..base import bigint

from datetime import datetime, timedelta, date

from sqlalchemy.orm import Mapped, mapped_column


class Users(Base):
    __tablename__ = "users"
    __table_args__ = {'schema': 'users'}

    user_id: Mapped[bigint] = mapped_column(primary_key=True, autoincrement=True)
    referal_count: Mapped[int] = mapped_column(default=0)

    passed_op: Mapped[bool] = mapped_column(default=False)
    from_group: Mapped[bool] = mapped_column(default=False)

    where_from: Mapped[str] = mapped_column(default="")
    reg_date: Mapped[date] = mapped_column(default=date.today)
    dead_date: Mapped[date] = mapped_column(default=None, nullable=True)
    dead: Mapped[bool] = mapped_column(default=False)

    age: Mapped[Optional[int]]
    is_man: Mapped[Optional[bool]]

    last_online: Mapped[datetime] = mapped_column(default=datetime.now)
    vip_time: Mapped[datetime] = mapped_column(default=datetime(1970, 1, 1), nullable=True)
    last_game: Mapped[datetime] = mapped_column(default=datetime(1970, 1, 1), nullable=True)
    banned: Mapped[bool] = mapped_column(default=False)

    @property
    def is_vip(self) -> bool:
        return (
            self.vip_time is not None
            and self.vip_time > datetime.now()
        )

    def add_vip(self, days: int = 0, hours: int = 0):
        """
        Add VIP days to user. You need to commit after.

        :param int days: Amount of days
        :param int hours: Amount if hours
        """

        self.vip_time = max(self.vip_time, datetime.now()) + timedelta(days=days, hours=hours)
