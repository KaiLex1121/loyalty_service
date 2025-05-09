from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config.main_config import DbConfig


def create_pool(db_config: DbConfig) -> async_sessionmaker[AsyncSession]:

    engine = create_async_engine(url=make_url(db_config.create_uri()))
    pool: async_sessionmaker[AsyncSession] = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    return pool
