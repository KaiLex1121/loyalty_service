import asyncio
import os
from typing import AsyncGenerator, Generator, Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command
from backend.core.settings import AppSettings, get_settings
from backend.main import app
from backend.db.base import Base
from backend.core.dependencies import get_db as app_get_db # Оригинальная зависимость get_db
from backend.models.account import Account # Для фикстуры пользователя
from backend.schemas.account import AccountCreate # Для создания пользователя
from backend.dao import HolderDAO # Для создания пользователя


# --- Настройка тестовой БД ---
# Загружаем настройки из .env.test
# Это гарантирует, что все тесты будут использовать тестовую конфигурацию
@pytest.fixture(scope="session")
def test_settings() -> AppSettings:
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, Any, None]:
    """
    Создает event loop для сессии pytest.
    Необходимо для асинхронных фикстур с областью видимости "session".
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_engine(test_settings: Settings):
    """
    Создает асинхронный движок SQLAlchemy для тестовой БД.
    Фикстура уровня сессии, т.е. движок создается один раз для всех тестов.
    """
    engine = create_async_engine(test_settings., echo=False) # echo=True для отладки SQL

    # Применяем миграции Alembic к тестовой БД
    # Это более надежно, чем Base.metadata.create_all()
    alembic_cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini")
    alembic_cfg = AlembicConfig(alembic_cfg_path)

    # Устанавливаем URL БД для Alembic из наших тестовых настроек
    # Это важно, чтобы Alembic работал с тестовой БД
    alembic_cfg.set_main_option("sqlalchemy.url", test_settings.DATABASE_URL)

    # Запускаем миграции до последней версии
    alembic_command.upgrade(alembic_cfg, "head")

    yield engine # Предоставляем движок тестам
    await engine.dispose() # Закрываем соединения движка


@pytest.fixture(scope="function") # function scope: сессия создается для каждого теста
async def db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Создает асинхронную сессию SQLAlchemy для каждого теста.
    Обеспечивает изоляцию тестов на уровне БД (откат транзакций).
    """
    connection = await test_db_engine.connect()
    transaction = await connection.begin() # Начинаем транзакцию

    # Создаем сессию, привязанную к этой транзакции
    TestingSessionLocal = sessionmaker(
        bind=connection, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
    )
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback() # Откатываем все изменения после теста
        await connection.close()


# --- Фикстура для FastAPI TestClient ---
@pytest.fixture(scope="function")
def client(db_session: AsyncSession, test_settings: Settings) -> Generator[TestClient, Any, None]:
    """
    Создает FastAPI TestClient, который использует тестовую сессию БД.
    """

    # Переопределяем зависимость get_settings для всего приложения на время теста
    # чтобы оно использовало тестовые настройки (включая SECRET_KEY для JWT)
    def override_get_settings() -> Settings:
        return test_settings

    app.dependency_overrides[app_get_settings] = override_get_settings


    # Переопределяем зависимость get_db, чтобы она возвращала нашу тестовую сессию
    def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session # Используем db_session из фикстуры

    app.dependency_overrides[app_get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    # Очищаем переопределения после теста, чтобы не влиять на другие тесты (если они есть вне этого client)
    app.dependency_overrides.clear()


# --- Вспомогательные фикстуры для тестов аутентификации ---
@pytest.fixture(scope="function")
async def test_user_data() -> dict:
    """Данные для создания тестового пользователя."""
    return {
        "username": "testuser@example.com", # Используем email как username для примера
        "password": "testpassword123"
    }

@pytest.fixture(scope="function")
async def test_user(db_session: AsyncSession, test_user_data: dict) -> User:
    """Создает тестового пользователя в БД."""
    user_in = UserCreate(username=test_user_data["username"], password=test_user_data["password"])
    user = await crud_user.create_user(db=db_session, user_in=user_in)
    return user


@pytest.fixture(scope="function")
async def auth_token(client: TestClient, test_user: User, test_user_data: dict) -> str:
    """
    Получает JWT токен для тестового пользователя.
    Зависит от фикстуры test_user, чтобы пользователь уже существовал.
    """
    login_data = {
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    }
    # Используем client для запроса к эндпоинту /auth/login
    # FastAPI TestClient автоматически обрабатывает form data для OAuth2PasswordRequestForm
    response = client.post("/auth/login", data=login_data)

    assert response.status_code == 200, f"Login failed: {response.json()}"
    token_data = response.json()
    assert "access_token" in token_data
    return token_data["access_token"]
