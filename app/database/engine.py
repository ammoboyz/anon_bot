import logging
import os

from app.utils.config import DB
from app.database.models import Base
from settings import DB_NANE

from sqlalchemy.engine import URL
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)


log = logging.getLogger('database.engine')

async def create_tables(engine: AsyncEngine) -> None:
    """
    Create tables from models.

    :param AsyncEngine engine: Async engine
    """

    async with engine.begin() as conn:
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS admins"))
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS users"))
        await conn.run_sync(Base.metadata.create_all)

        log.info('Tables created successfully')


async def create_sessionmaker(database: DB) -> async_sessionmaker:
    """
    Create an async sessionmaker for the database and create tables if they don't exist.

    :param str database: Postgres database credentials
    :param bool debug: Debug mode, defaults to False
    :return async_sessionmaker: Async sessionmaker (sessionmaker with AsyncSession class)
    """

    engine = create_async_engine(
        URL(
            'postgresql+asyncpg',
            database.user,
            database.password,
            database.host,
            database.port,
            DB_NANE,
            query={},
        ), future=True,
        pool_size=20,
    )
    log.info('Connected to database')

    await create_tables(engine)
    return async_sessionmaker(engine, expire_on_commit=False)
