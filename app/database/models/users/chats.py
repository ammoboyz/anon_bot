from datetime import date
from sqlalchemy.orm import Mapped, mapped_column

from .. import Base
from ..base import bigint


class Chats(Base):
    __tablename__ = "chats"
    __table_args__ = {'schema': 'users'}

    chat_id: Mapped[bigint] = mapped_column(primary_key=True, autoincrement=True)
    reg_date: Mapped[date] = mapped_column(default=date.today)
