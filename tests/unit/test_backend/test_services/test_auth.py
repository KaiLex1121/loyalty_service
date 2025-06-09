from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, status

from backend.enums.back_office import OtpPurposeEnum
from backend.schemas.auth import OTPVerifyRequest
from backend.services.auth import AuthService


class TestAuthService:

    @pytest.fixture
    def mock_dao() -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_account():
        return MagicMock(id=1, phone_number="+79999999999", is_active=False)

    @pytest.fixture
    def mock_active_otp():
        otp = MagicMock()
        otp.hashed_code = (
            "03d157a32f88465808e4081933c705bc60686637ee7c11d8464bf1d782b36570"
        )
        otp.is_expired = False
        return otp

    @pytest.fixture
    def mock_services(mock_account, mock_active_otp, mock_session, test_settings):
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
            settings=test_settings,
        )
        return auth_service, mock_session, dao, mock_account, mock_active_otp

    @pytest.mark.asyncio
    async def test_verify_otp_and_login_success(
        self,
        mock_services: tuple[AuthService, AsyncMock, MagicMock, Any, Any],
    ):
        auth_service, session, dao, _, _ = mock_services
        otp_data = OTPVerifyRequest(
            otp_code="123456",
            purpose=OtpPurposeEnum.BACKOFFICE_LOGIN,
            phone_number="+79999999999",
        )
        token = await auth_service.verify_otp_and_login(session, dao, otp_data)
        assert isinstance(token, str)
        assert len(token) > 10

    @pytest.mark.asyncio
    async def test_verify_otp_and_login_invalid_otp(
        self,
        mock_services: tuple[AuthService, AsyncMock, MagicMock, Any, Any],
    ):
        auth_service, session, dao, _, mock_active_otp = mock_services
        otp_data = OTPVerifyRequest(
            otp_code="654321",
            purpose=OtpPurposeEnum.BACKOFFICE_LOGIN,
            phone_number="+79999999999",
        )
        # emulate wrong hash compare
        mock_active_otp.hashed_code = "another_hash"

        with pytest.raises(HTTPException) as excinfo:
            await auth_service.verify_otp_and_login(session, dao, otp_data)
        assert excinfo.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid OTP code" in excinfo.value.detail

    @pytest.mark.asyncio
    async def test_request_otp_for_login_success(
        self,
        mock_services: tuple[AuthService, AsyncMock, MagicMock, Any, Any],
    ):
        auth_service, session, dao, mock_account, _ = mock_services
        phone_number = "+79999999999"
        auth_service.account_service.get_or_create_account = AsyncMock(
            return_value=mock_account
        )
        auth_service.otp_code_service.invalidate_previous_otps = AsyncMock()
        auth_service.otp_code_service.create_otp = AsyncMock()

        result = await auth_service.request_otp_for_login(session, dao, phone_number)
        assert result is mock_account

    @pytest.mark.asyncio
    async def test_request_otp_for_login_send_otp_fail(
        self,
        mock_services: tuple[AuthService, AsyncMock, MagicMock, Any, Any],
    ):
        auth_service, session, dao, mock_account, _ = mock_services
        phone_number = "+79999999999"
        auth_service.account_service.get_or_create_account = AsyncMock(
            return_value=mock_account
        )
        auth_service.otp_code_service.invalidate_previous_otps = AsyncMock()
        auth_service.otp_code_service.create_otp = AsyncMock()
        auth_service.otp_sending_service.send_otp.return_value = False

        with pytest.raises(HTTPException) as excinfo:
            await auth_service.request_otp_for_login(session, dao, phone_number)
        assert excinfo.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "Could not send OTP SMS" in excinfo.value.detail
