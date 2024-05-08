from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column

from .. import Base
from ..base import bigint


class Queue(Base):
    __tablename__ = "queue"
    __table_args__ = {'schema': 'users'}

    user_id: Mapped[bigint] = mapped_column(primary_key=True, autoincrement=True)

    is_man: Mapped[bool] = mapped_column(default=False)
    target_man: Mapped[Optional[bool]]

    age: Mapped[int] = mapped_column(default=0)
    room: Mapped[str] = mapped_column(default="")
