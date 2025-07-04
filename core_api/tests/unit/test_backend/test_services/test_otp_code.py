from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.holder import HolderDAO
from app.models.account import Account
from app.models.otp_code import OtpCode
from app.schemas.otp_code import OtpCodeCreate
from app.services.otp_code import OtpCodeService


@pytest.fixture
def otp_service():
    """Fixture to create OtpCodeService instance"""
    return OtpCodeService()


@pytest.fixture
def mock_session():
    """Fixture to create mock AsyncSession"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_dao():
    """Fixture to create mock HolderDAO"""
    dao = MagicMock(spec=HolderDAO)
    dao.otp_code = AsyncMock()
    return dao


@pytest.fixture
def mock_account():
    """Fixture to create mock Account"""
    account = MagicMock(spec=Account)
    account.id = 123
    account.email = "test@example.com"
    return account


@pytest.fixture
def mock_otp_code():
    """Fixture to create mock OtpCode"""
    otp = MagicMock(spec=OtpCode)
    otp.id = 456
    otp.code = "123456"
    otp.purpose = "backoffice_login"
    otp.account_id = 123
    otp.created_at = datetime.now()
    otp.expires_at = datetime.now()
    otp.is_used = False
    return otp


@pytest.fixture
def mock_otp_create():
    """Fixture to create mock OtpCodeCreate schema"""
    return OtpCodeCreate(
        account_id=123,
        hashed_code="hashed_123456",
        purpose="backoffice_login",
        expires_at=datetime.now(),
        channel="tg",
    )


class TestOtpCodeService:
    """Test suite for OtpCodeService"""

    # POSITIVE TESTS
    class TestPositiveCases:
        """Test positive scenarios where operations succeed"""

        @pytest.mark.asyncio
        async def test_invalidate_previous_otps_success(
            self,
            otp_service,
            mock_session: AsyncMock,
            mock_dao: MagicMock,
            mock_account: MagicMock,
        ):
            """Test successful invalidation of previous OTPs"""
            # Arrange
            purpose = "login"
            mock_dao.otp_code.invalidate_previous_otps.return_value = None

            # Act
            result = await otp_service.invalidate_previous_otps(
                mock_session, mock_dao, mock_account, purpose
            )

            # Assert
            assert result is None
            mock_dao.otp_code.invalidate_previous_otps.assert_called_once_with(
                mock_session, account_id=mock_account.id, purpose=purpose
            )

        @pytest.mark.asyncio
        async def test_create_otp_success(
            self,
            otp_service: OtpCodeService,
            mock_session: AsyncMock,
            mock_dao: MagicMock,
            mock_otp_create: MagicMock,
            mock_otp_code: MagicMock,
        ):
            """Test successful OTP creation"""
            # Arrange
            mock_dao.otp_code.create = AsyncMock(return_value=mock_otp_code)

            # Act
            result = await otp_service.create_otp(
                mock_session, mock_dao, mock_otp_create
            )

            # Assert
            assert result == mock_otp_code
            mock_dao.otp_code.create.assert_called_once_with(
                mock_session, obj_in=mock_otp_create
            )

        @pytest.mark.asyncio
        async def test_set_mark_otp_as_used_success(
            self,
            otp_service,
            mock_session: AsyncMock,
            mock_dao: MagicMock,
            mock_otp_code,
        ):
            """Test successful marking of OTP as used"""
            # Arrange
            mock_dao.otp_code.mark_otp_as_used.return_value = None

            # Act
            result = await otp_service.set_mark_otp_as_used(
                mock_session, mock_dao, mock_otp_code
            )

            # Assert
            assert result is None
            mock_dao.otp_code.mark_otp_as_used.assert_called_once_with(
                mock_session, otp_obj=mock_otp_code
            )

        @pytest.mark.asyncio
        async def test_multiple_operations_sequence(
            self,
            otp_service,
            mock_session: AsyncMock,
            mock_dao: MagicMock,
            mock_account: MagicMock,
            mock_otp_create,
            mock_otp_code,
        ):
            """Test successful sequence of multiple operations"""
            # Arrange
            purpose = "password_reset"
            mock_dao.otp_code.invalidate_previous_otps.return_value = None
            mock_dao.otp_code.create.return_value = mock_otp_code

            # Act - Invalidate previous OTPs
            await otp_service.invalidate_previous_otps(
                mock_session, mock_dao, mock_account, purpose
            )

            # Act - Create new OTP
            new_otp = await otp_service.create_otp(
                mock_session, mock_dao, mock_otp_create
            )

            # Assert
            mock_dao.otp_code.invalidate_previous_otps.assert_called_once()
            mock_dao.otp_code.create.assert_called_once()
            assert new_otp == mock_otp_code

    # NEGATIVE TESTS
    class TestNegativeCases:
        """Test negative scenarios with invalid inputs"""

        @pytest.mark.asyncio
        async def test_invalidate_previous_otps_with_none_account(
            self, otp_service, mock_session: AsyncMock, mock_dao: MagicMock
        ):
            """Test invalidation with None account"""
            # Arrange
            purpose = "login"

            # Act & Assert
            with pytest.raises(AttributeError):
                await otp_service.invalidate_previous_otps(
                    mock_session, mock_dao, None, purpose
                )

        @pytest.mark.asyncio
        async def test_invalidate_previous_otps_with_empty_purpose(
            self,
            otp_service: OtpCodeService,
            mock_session: AsyncMock,
            mock_dao: MagicMock,
            mock_account: MagicMock,
        ):
            """Test invalidation with empty purpose"""
            # Arrange
            purpose = ""
            mock_dao.otp_code.invalidate_previous_otps.return_value = None

            # Act
            await otp_service.invalidate_previous_otps(
                mock_session, mock_dao, mock_account, purpose
            )

            # Assert - Should still call the DAO method
            mock_dao.otp_code.invalidate_previous_otps.assert_called_once_with(
                mock_session, account_id=mock_account.id, purpose=purpose
            )

        @pytest.mark.asyncio
        async def test_create_otp_with_none_schema(
            self,
            otp_service: OtpCodeService,
            mock_session: AsyncMock,
            mock_dao: MagicMock,
        ):
            """Test OTP creation with None schema"""
            # Act & Assert
            with pytest.raises((AttributeError, TypeError, ValueError)):
                await otp_service.create_otp(mock_session, mock_dao, None)

        @pytest.mark.asyncio
        async def test_set_mark_otp_as_used_with_none_otp(
            self,
            otp_service: OtpCodeService,
            mock_session: AsyncMock,
            mock_dao: MagicMock,
        ):
            """Test marking OTP as used with None OTP object"""
            # Act & Assert
            with pytest.raises((AttributeError, TypeError)):
                await otp_service.set_mark_otp_as_used(mock_session, mock_dao, None)

    # EXCEPTION TESTS
    class TestExceptionHandling:
        """Test exception scenarios and error handling"""

        @pytest.mark.asyncio
        async def test_invalidate_previous_otps_database_error(
            self,
            otp_service,
            mock_session: AsyncMock,
            mock_dao: MagicMock,
            mock_account,
        ):
            """Test database error during OTP invalidation"""
            # Arrange
            purpose = "login"
            mock_dao.otp_code.invalidate_previous_otps.side_effect = SQLAlchemyError(
                "Database connection failed"
            )

            # Act & Assert
            with pytest.raises(SQLAlchemyError) as exc_info:
                await otp_service.invalidate_previous_otps(
                    mock_session, mock_dao, mock_account, purpose
                )

            assert "Database connection failed" in str(exc_info.value)
            mock_dao.otp_code.invalidate_previous_otps.assert_called_once()

        @pytest.mark.asyncio
        async def test_create_otp_integrity_error(
            self,
            otp_service,
            mock_session: AsyncMock,
            mock_dao: MagicMock,
            mock_otp_create,
        ):
            """Test integrity constraint violation during OTP creation"""
            # Arrange
            mock_dao.otp_code.create.side_effect = IntegrityError(
                "Duplicate key violation", None, None
            )

            # Act & Assert
            with pytest.raises(IntegrityError) as exc_info:
                await otp_service.create_otp(mock_session, mock_dao, mock_otp_create)

            assert "Duplicate key violation" in str(exc_info.value)
            mock_dao.otp_code.create.assert_called_once()

        @pytest.mark.asyncio
        async def test_set_mark_otp_as_used_database_error(
            self,
            otp_service,
            mock_session: AsyncMock,
            mock_dao: MagicMock,
            mock_otp_code,
        ):
            """Test database error when marking OTP as used"""
            # Arrange
            mock_dao.otp_code.mark_otp_as_used.side_effect = SQLAlchemyError(
                "Connection timeout"
            )

            # Act & Assert
            with pytest.raises(SQLAlchemyError) as exc_info:
                await otp_service.set_mark_otp_as_used(
                    mock_session, mock_dao, mock_otp_code
                )

            assert "Connection timeout" in str(exc_info.value)
            mock_dao.otp_code.mark_otp_as_used.assert_called_once()

        @pytest.mark.asyncio
        async def test_create_otp_generic_exception(
            self,
            otp_service,
            mock_session: AsyncMock,
            mock_dao: MagicMock,
            mock_otp_create,
        ):
            """Test generic exception during OTP creation"""
            # Arrange
            mock_dao.otp_code.create.side_effect = Exception("Unexpected error")

            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await otp_service.create_otp(mock_session, mock_dao, mock_otp_create)

            assert "Unexpected error" in str(exc_info.value)

        @pytest.mark.asyncio
        async def test_invalidate_previous_otps_timeout(
            self,
            otp_service,
            mock_session: AsyncMock,
            mock_dao: MagicMock,
            mock_account,
        ):
            """Test timeout during OTP invalidation"""
            # Arrange
            purpose = "login"
            mock_dao.otp_code.invalidate_previous_otps.side_effect = TimeoutError(
                "Operation timed out"
            )

            # Act & Assert
            with pytest.raises(TimeoutError) as exc_info:
                await otp_service.invalidate_previous_otps(
                    mock_session, mock_dao, mock_account, purpose
                )

            assert "Operation timed out" in str(exc_info.value)

        @pytest.mark.asyncio
        async def test_dao_method_not_found(
            self, otp_service, mock_session: AsyncMock, mock_account
        ):
            """Test when DAO doesn't have expected methods"""
            # Arrange
            invalid_dao = MagicMock()
            # Remove the otp_code attribute to simulate missing method
            del invalid_dao.otp_code
            purpose = "login"

            # Act & Assert
            with pytest.raises(AttributeError):
                await otp_service.invalidate_previous_otps(
                    mock_session, invalid_dao, mock_account, purpose
                )

    # EDGE CASES
    class TestEdgeCases:
        """Test edge cases and boundary conditions"""

        @pytest.mark.asyncio
        async def test_invalidate_with_special_characters_in_purpose(
            self,
            otp_service,
            mock_session: AsyncMock,
            mock_dao: MagicMock,
            mock_account,
        ):
            """Test invalidation with special characters in purpose"""
            # Arrange
            purpose = "login@#$%^&*()"
            mock_dao.otp_code.invalidate_previous_otps.return_value = None

            # Act
            await otp_service.invalidate_previous_otps(
                mock_session, mock_dao, mock_account, purpose
            )

            # Assert
            mock_dao.otp_code.invalidate_previous_otps.assert_called_once_with(
                mock_session, account_id=mock_account.id, purpose=purpose
            )

        @pytest.mark.asyncio
        async def test_invalidate_with_very_long_purpose(
            self,
            otp_service,
            mock_session: AsyncMock,
            mock_dao: MagicMock,
            mock_account,
        ):
            """Test invalidation with extremely long purpose string"""
            # Arrange
            purpose = "x" * 1000  # Very long string
            mock_dao.otp_code.invalidate_previous_otps.return_value = None

            # Act
            await otp_service.invalidate_previous_otps(
                mock_session, mock_dao, mock_account, purpose
            )

            # Assert
            mock_dao.otp_code.invalidate_previous_otps.assert_called_once_with(
                mock_session, account_id=mock_account.id, purpose=purpose
            )

        @pytest.mark.asyncio
        async def test_create_otp_returns_none(
            self,
            otp_service,
            mock_session: AsyncMock,
            mock_dao: MagicMock,
            mock_otp_create,
        ):
            """Test when DAO create method returns None"""
            # Arrange
            mock_dao.otp_code.create.return_value = None

            # Act
            result = await otp_service.create_otp(
                mock_session, mock_dao, mock_otp_create
            )

            # Assert
            assert result is None
            mock_dao.otp_code.create.assert_called_once()


# PERFORMANCE TESTS
class TestOtpCodeServicePerformance:
    """Performance and concurrency tests"""

    @pytest.mark.asyncio
    async def test_concurrent_otp_operations(self):
        """Test concurrent OTP operations"""
        import asyncio

        # Arrange
        otp_service = OtpCodeService()
        mock_session = AsyncMock(spec=AsyncSession)
        mock_dao = MagicMock(spec=HolderDAO)
        mock_dao.otp_code = AsyncMock()

        mock_account = MagicMock(spec=Account)
        mock_account.id = 123

        # Configure mock to simulate delay
        async def mock_invalidate(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate database delay
            return None

        mock_dao.otp_code.invalidate_previous_otps.side_effect = mock_invalidate

        # Act - Run multiple concurrent operations
        tasks = [
            otp_service.invalidate_previous_otps(
                mock_session, mock_dao, mock_account, f"purpose_{i}"
            )
            for i in range(5)
        ]

        start_time = datetime.now()
        await asyncio.gather(*tasks)
        end_time = datetime.now()

        # Assert - Operations should run concurrently
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 0.5  # Should be less than sequential execution
        assert mock_dao.otp_code.invalidate_previous_otps.call_count == 5
