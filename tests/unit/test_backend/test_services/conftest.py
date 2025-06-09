from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.dao.holder import HolderDAO
from backend.services.auth import AuthService


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
