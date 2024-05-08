from datetime import datetime
from typing import Optional

from .. import Base
from ..base import bigint
from .users import Users

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class Profile(Base):
    __tablename__ = 'profile'
    __table_args__ = {'schema': 'users'}

    user_id: Mapped[bigint] = mapped_column(ForeignKey(Users.user_id), primary_key=True)

    fire: Mapped[int] = mapped_column(default=0)
    satan: Mapped[int] = mapped_column(default=0)
    clown: Mapped[int] = mapped_column(default=0)
    shit: Mapped[int] = mapped_column(default=0)

    time_in_chats: Mapped[int] = mapped_column(default=0)
    message_count: Mapped[int] = mapped_column(default=0)
    dialogue_count: Mapped[int] = mapped_column(default=0)
    anon_count: Mapped[int] = mapped_column(default=0)
    swear_count: Mapped[int] = mapped_column(default=0)

    interests: Mapped[str] = mapped_column(default="[]")
    friends: Mapped[str] = mapped_column(default="[]")

    target_man: Mapped[Optional[bool]] = mapped_column(default=None, nullable=True)
    target_age: Mapped[str] = mapped_column(default="[]", nullable=True)
    target_room: Mapped[str] = mapped_column(default="")
