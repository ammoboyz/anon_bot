from datetime import datetime

from .. import Base
from ..base import bigint
from .users import Users

from typing import Optional

from sqlalchemy import ForeignKey, or_, select, delete
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession


class Dialogues(Base):
    __tablename__ = 'dialogues'
    __table_args__ = {'schema': 'users'}

    first: Mapped[bigint] = mapped_column(ForeignKey(Users.user_id), primary_key=True)
    second: Mapped[bigint] = mapped_column(ForeignKey(Users.user_id), primary_key=True)
    start_dialogue: Mapped[datetime] = mapped_column(default=datetime.now)


    @classmethod
    async def delete_dialogue(cls, session: AsyncSession, user_id: int):
        await session.execute(
            delete(cls)
            .where(
                or_(
                    cls.first == user_id,
                    cls.second == user_id,
                ),
            )
        )


    @classmethod
    async def get_dialogue(cls, user_id: int, session: AsyncSession) -> Optional["Dialogues"]:
        return await session.scalar(
            select(cls)
            .where(or_(
                cls.first == user_id,
                cls.second == user_id
            ))
        )

    def second_id(self, first: int) -> int:
        return self.first if first == self.second else self.second