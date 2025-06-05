from unittest.mock import AsyncMock, MagicMock

import pytest

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
    return session


@pytest.fixture
def mock_account():
    return MagicMock(id=1, phone_number="+79999999999", is_active=False)


@pytest.fixture
def mock_active_otp():
    otp = MagicMock()
    otp.hashed_code = "03d157a32f88465808e4081933c705bc60686637ee7c11d8464bf1d782b36570"
    otp.is_expired = False
    return otp


@pytest.fixture
def mock_services(mock_account, mock_active_otp, mock_session):
    account_service = AsyncMock()
    account_service.get_account_by_phone.return_value = mock_account
    account_service.set_account_as_active.return_value = None

    otp_code_service = AsyncMock()
    otp_code_service.set_mark_otp_as_used.return_value = None

    otp_sending_service = AsyncMock()
    otp_sending_service.send_otp.return_value = True

    dao = MagicMock()
    dao.otp_code.get_active_otp_by_account_and_purpose = AsyncMock(
        return_value=mock_active_otp
    )

    auth_service = AuthService(
        account_service=account_service,
        otp_code_service=otp_code_service,
        otp_sending_service=otp_sending_service,
    )
    return auth_service, mock_session, dao, mock_account, mock_active_otp
