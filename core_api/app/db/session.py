from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.settings import AppSettings


def create_pool(config: AppSettings) -> async_sessionmaker[AsyncSession]:
    db_uri = config.DB.DATABASE_URI
    engine = create_async_engine(url=make_url(str(db_uri)))
    pool: async_sessionmaker[AsyncSession] = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    return pool
