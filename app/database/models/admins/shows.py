from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey

from .. import Base
from .sponsors import Sponsors
from ..base import bigint


class Shows(Base):
    __tablename__ = "shows"
    __table_args__ = {'schema': 'admins'}

    id: Mapped[bigint] = mapped_column(autoincrement=True, primary_key=True)

    name: Mapped[str] = mapped_column(default="")
    from_chat_id: Mapped[bigint] = mapped_column(default=0)
    message_id: Mapped[bigint] = mapped_column(default=0)
    markup: Mapped[Optional[str]] = mapped_column(default="")

    views: Mapped[int] = mapped_column(default=0)
    views_limit: Mapped[bigint] = mapped_column(default=0)
    is_actual: Mapped[bool] = mapped_column(default=True)
    is_hello: Mapped[bool] = mapped_column(default=False)

    create_date: Mapped[datetime] = mapped_column(default=datetime.now)
