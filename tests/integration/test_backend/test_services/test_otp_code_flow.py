from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.account import Account
from backend.models.otp_code import OtpCode
from backend.schemas.otp_code import OtpCodeCreate
from backend.services.otp_code import OtpCodeService


class TestOtpCodeServiceIntegration:

    @pytest.fixture
    def otp_service(self):
        return OtpCodeService()

    @pytest.mark.asyncio
    async def test_complete_otp_workflow(
        self, mock_session: AsyncSession, mock_dao: MagicMock
    ):
        """Test complete OTP workflow from invalidation to creation to usage"""
        # Arrange
        otp_service = OtpCodeService()
        mock_dao.otp_code = AsyncMock()

        mock_account = MagicMock(spec=Account)
        mock_account.id = 123

        mock_otp_create = OtpCodeCreate(
            account_id=123,
            channel="tg",
            hashed_code="hashed_123456",
            purpose="backoffice_login",
            expires_at=datetime.now(),
        )

        mock_otp_code = MagicMock(spec=OtpCode)
        mock_otp_code.id = 456

        # Configure mocks
        mock_dao.otp_code.invalidate_previous_otps.return_value = None
        mock_dao.otp_code.create.return_value = mock_otp_code
        mock_dao.otp_code.mark_otp_as_used.return_value = None

        # Act - Complete workflow
        # Step 1: Invalidate previous OTPs
        await otp_service.invalidate_previous_otps(
            mock_session, mock_dao, mock_account, "login"
        )

        # Step 2: Create new OTP
        new_otp = await otp_service.create_otp(mock_session, mock_dao, mock_otp_create)

        # Step 3: Mark OTP as used
        await otp_service.set_mark_otp_as_used(mock_session, mock_dao, new_otp)

        # Assert
        mock_dao.otp_code.invalidate_previous_otps.assert_called_once()
        mock_dao.otp_code.create.assert_called_once()
        mock_dao.otp_code.mark_otp_as_used.assert_called_once_with(
            mock_session, otp_obj=new_otp
        )
        assert new_otp == mock_otp_code
