import asyncio
import os
from typing import Any, AsyncGenerator, Generator, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.core.dependencies import get_session as app_get_db
from backend.core.settings import AppSettings, get_settings
from backend.dao.holder import HolderDAO
from backend.db.base import Base
from backend.main import app


class DummyAsyncContextManager:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.begin = MagicMock(return_value=DummyAsyncContextManager())
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def mock_dao():
    dao = MagicMock(spec=HolderDAO)
    return dao


@pytest.fixture(scope="session")
def test_settings() -> AppSettings:
    get_settings.cache_clear()
    return get_settings()


@pytest_asyncio.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, Any, None]:
    """
    Создает event loop для сессии pytest.
    Необходимо для асинхронных фикстур с областью видимости "session".
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def database_engine(
    test_settings: AppSettings,
) -> AsyncGenerator[AsyncEngine, None]:
    TEST_DB_URI = test_settings.DB.DATABASE_URI
    engine = create_async_engine(TEST_DB_URI)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def session_factory(
    database_engine: database_engine,
) -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    pool: async_sessionmaker[AsyncSession] = async_sessionmaker(
        bind=database_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    yield pool


@pytest_asyncio.fixture(scope="session")
async def setup_database_with_migrations(test_settings: AppSettings):
    alembic_cfg_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "alembic.ini"
    )
    alembic_cfg = AlembicConfig(alembic_cfg_path)
    alembic_cfg.set_main_option("sqlalchemy.url", test_settings.DB.DATABASE_URI)
    alembic_command.upgrade(alembic_cfg, "head")
    yield
    alembic_command.downgrade(alembic_cfg, "base")


@pytest_asyncio.fixture(scope="session")
async def setup_database_without_migrations(session_factory: session_factory):

    async with session_factory.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with session_factory.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(
    scope="function"
)  # function scope: сессия создается для каждого теста
async def test_db_session(
    session_factory: session_factory,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Создает асинхронную сессию SQLAlchemy для каждого теста.
    Обеспечивает изоляцию тестов на уровне БД (откат транзакций).
    """
    async with session_factory() as session:
        transaction = await session.begin()
        try:
            yield session
        finally:
            await transaction.rollback()


# --- Фикстура для FastAPI TestClient ---
@pytest_asyncio.fixture(scope="function")
async def client(
    test_db_session: AsyncSession, test_settings: AppSettings
) -> AsyncGenerator[AsyncClient | Any, None]:
    """
    Создает FastAPI TestClient, который использует тестовую сессию БД.
    """

    async def override_get_settings() -> AsyncGenerator[AppSettings, None]:
        yield test_settings

    app.dependency_overrides[get_settings] = override_get_settings

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db_session

    app.dependency_overrides[app_get_db] = override_get_db

    async with AsyncClient(app, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()
