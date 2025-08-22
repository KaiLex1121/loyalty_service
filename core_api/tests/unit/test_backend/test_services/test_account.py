from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.dao.holder import HolderDAO
from app.models.account import Account
from app.schemas.account import AccountUpdate
from app.services.account import AccountService
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


class TestAccountService:
    """Test suite for AccountService"""

    @pytest.fixture
    def service(self):
        """Create AccountService instance for testing"""
        return AccountService()

    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_dao(self):
        """Create mock DAO holder"""
        dao = MagicMock(spec=HolderDAO)
        dao.account = AsyncMock()
        return dao

    @pytest.fixture
    def sample_account(self):
        """Create sample account for testing"""
        return Account(
            id=1,
            phone_number="+1234567890",
            email="test@example.com",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    # ==================== POSITIVE TESTS ====================

    @pytest.mark.asyncio
    async def test_get_account_by_phone_success(
        self, service, mock_db, mock_dao, sample_account
    ):
        """Test successful retrieval of account by phone number"""
        # Arrange
        phone_number = "+1234567890"
        mock_dao.account.get_by_phone_number_without_relations.return_value = (
            sample_account
        )

        # Act
        result = await service.get_account_by_phone(mock_db, mock_dao, phone_number)

        # Assert
        assert result == sample_account
        mock_dao.account.get_by_phone_number_without_relations.assert_called_once_with(
            mock_db, phone_number=phone_number
        )

    @pytest.mark.asyncio
    async def test_get_account_by_id_success(
        self, service, mock_db, mock_dao, sample_account
    ):
        """Test successful retrieval of account by ID"""
        # Arrange
        account_id = 1
        mock_dao.account.get.return_value = sample_account

        # Act
        result = await service.get_account_by_id(mock_db, mock_dao, account_id)

        # Assert
        assert result == sample_account
        mock_dao.account.get.assert_called_once_with(mock_db, account_id=account_id)

    @pytest.mark.asyncio
    async def test_create_account_success_with_email(
        self, service, mock_db, mock_dao, sample_account
    ):
        """Test successful account creation with email"""
        # Arrange
        phone_number = "+1234567890"
        email = "test@example.com"
        mock_dao.account.create.return_value = sample_account

        # Act
        result = await service.create_account(mock_db, mock_dao, phone_number, email)

        # Assert
        assert result == sample_account
        mock_dao.account.create.assert_called_once()

        # Verify the AccountCreate object passed to create method
        call_args = mock_dao.account.create.call_args
        account_create = call_args[1]["obj_in"]
        assert account_create.phone_number == phone_number
        assert account_create.email == email
        assert account_create.is_active is False

    @pytest.mark.asyncio
    async def test_create_account_success_without_email(
        self, service, mock_db, mock_dao, sample_account
    ):
        """Test successful account creation without email"""
        # Arrange
        phone_number = "+1234567890"
        mock_dao.account.create.return_value = sample_account

        # Act
        result = await service.create_account(mock_db, mock_dao, phone_number)

        # Assert
        assert result == sample_account
        call_args = mock_dao.account.create.call_args
        account_create = call_args[1]["obj_in"]
        assert account_create.phone_number == phone_number
        assert account_create.email is None
        assert account_create.is_active is False

    @pytest.mark.asyncio
    async def test_get_or_create_account_existing_account(
        self, service, mock_db, mock_dao, sample_account
    ):
        """Test get_or_create when account already exists"""
        # Arrange
        phone_number = "+1234567890"
        mock_dao.account.get_by_phone_number_without_relations.return_value = (
            sample_account
        )

        # Act
        result = await service.get_or_create_account(mock_db, mock_dao, phone_number)

        # Assert
        assert result == sample_account
        mock_dao.account.get_by_phone_number_without_relations.assert_called_once()
        mock_dao.account.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_create_account_new_account(
        self, service, mock_db, mock_dao, sample_account
    ):
        """Test get_or_create when account doesn't exist"""
        # Arrange
        phone_number = "+1234567890"
        mock_dao.account.get_by_phone_number_without_relations.return_value = None
        mock_dao.account.create.return_value = sample_account

        # Act
        result = await service.get_or_create_account(mock_db, mock_dao, phone_number)

        # Assert
        assert result == sample_account
        mock_dao.account.get_by_phone_number_without_relations.assert_called_once()
        mock_dao.account.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_account_as_active_success(self, service, sample_account):
        """Test successful activation of account"""
        # Arrange
        sample_account.is_active = False

        # Act
        result = await service.set_account_as_active(sample_account)

        # Assert
        assert result.is_active is True
        assert result == sample_account

    @pytest.mark.asyncio
    async def test_update_account_success(
        self, service, mock_db, mock_dao, sample_account
    ):
        """Test successful account update"""
        # Arrange
        account_update = AccountUpdate(email="updated@example.com")
        data = {
            k: v
            for k, v in sample_account.__dict__.items()
            if k != "_sa_instance_state"
        }
        updated_account = Account(**data)
        updated_account.email = "updated@example.com"

        mock_dao.account.update.return_value = updated_account

        # Act
        result = await service.update_account(
            mock_db, mock_dao, sample_account, account_update
        )

        # Assert
        assert result == updated_account
        mock_dao.account.update.assert_called_once_with(
            mock_db, db_obj=sample_account, obj_in=account_update
        )
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_called_once_with(updated_account)

    # ==================== NEGATIVE TESTS ====================

    @pytest.mark.asyncio
    async def test_get_account_by_phone_not_found(self, service, mock_db, mock_dao):
        """Test get_account_by_phone when account doesn't exist"""
        # Arrange
        phone_number = "+1234567890"
        mock_dao.account.get_by_phone_number_without_relations.return_value = None

        # Act
        result = await service.get_account_by_phone(mock_db, mock_dao, phone_number)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_account_by_id_not_found(self, service, mock_db, mock_dao):
        """Test get_account_by_id raises exception when account doesn't exist"""
        # Arrange
        account_id = 999
        mock_dao.account.get.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.get_account_by_id(mock_db, mock_dao, account_id)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "account not found"

    @pytest.mark.asyncio
    async def test_get_account_by_phone_dao_exception(self, service, mock_db, mock_dao):
        """Test get_account_by_phone when DAO raises exception"""
        # Arrange
        phone_number = "+1234567890"
        mock_dao.account.get_by_phone_number_without_relations.side_effect = Exception(
            "Database error"
        )

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await service.get_account_by_phone(mock_db, mock_dao, phone_number)

        assert str(exc_info.value) == "Database error"

    @pytest.mark.asyncio
    async def test_create_account_dao_exception(self, service, mock_db, mock_dao):
        """Test create_account when DAO raises exception"""
        # Arrange
        phone_number = "+1234567890"
        mock_dao.account.create.side_effect = Exception("Creation failed")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await service.create_account(mock_db, mock_dao, phone_number)

        assert str(exc_info.value) == "Creation failed"

    @pytest.mark.asyncio
    async def test_update_account_dao_exception(
        self, service, mock_db, mock_dao, sample_account
    ):
        """Test update_account when DAO raises exception"""
        # Arrange
        account_update = AccountUpdate(email="updated@example.com")
        mock_dao.account.update.side_effect = Exception("Update failed")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await service.update_account(
                mock_db, mock_dao, sample_account, account_update
            )

        assert str(exc_info.value) == "Update failed"

    @pytest.mark.asyncio
    async def test_update_account_flush_exception(
        self, service, mock_db, mock_dao, sample_account
    ):
        """Test update_account when db.flush() raises exception"""
        # Arrange
        account_update = AccountUpdate(email="updated@example.com")
        data = {
            k: v
            for k, v in sample_account.__dict__.items()
            if k != "_sa_instance_state"
        }
        updated_account = Account(**data)
        mock_dao.account.update.return_value = updated_account
        mock_db.flush.side_effect = Exception("Flush failed")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await service.update_account(
                mock_db, mock_dao, sample_account, account_update
            )

        assert str(exc_info.value) == "Flush failed"

    # ==================== EDGE CASES / EXCEPTION TESTS ====================

    @pytest.mark.asyncio
    async def test_get_account_by_phone_empty_string(self, service, mock_db, mock_dao):
        """Test get_account_by_phone with empty phone number"""
        # Arrange
        phone_number = ""
        mock_dao.account.get_by_phone_number_without_relations.return_value = None

        # Act
        result = await service.get_account_by_phone(mock_db, mock_dao, phone_number)

        # Assert
        assert result is None
        mock_dao.account.get_by_phone_number_without_relations.assert_called_once_with(
            mock_db, phone_number=""
        )

    @pytest.mark.asyncio
    async def test_get_account_by_id_zero(self, service, mock_db, mock_dao):
        """Test get_account_by_id with ID of 0"""
        # Arrange
        account_id = 0
        mock_dao.account.get.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.get_account_by_id(mock_db, mock_dao, account_id)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_account_by_id_negative(self, service, mock_db, mock_dao):
        """Test get_account_by_id with negative ID"""
        # Arrange
        account_id = -1
        mock_dao.account.get.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.get_account_by_id(mock_db, mock_dao, account_id)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_create_account_empty_phone_number(
        self, service, mock_db, mock_dao, sample_account
    ):
        """Test create_account with empty phone number"""
        # Arrange
        phone_number = ""
        mock_dao.account.create.return_value = sample_account

        # Act
        result = await service.create_account(mock_db, mock_dao, phone_number)

        # Assert
        assert result == sample_account
        call_args = mock_dao.account.create.call_args
        account_create = call_args[1]["obj_in"]
        assert account_create.phone_number == ""

    @pytest.mark.asyncio
    async def test_set_account_as_active_already_active(self, service, sample_account):
        """Test set_account_as_active when account is already active"""
        # Arrange
        sample_account.is_active = True

        # Act
        result = await service.set_account_as_active(sample_account)

        # Assert
        assert result.is_active is True
        assert result == sample_account

    @pytest.mark.asyncio
    async def test_update_account_empty_update(
        self, service, mock_db, mock_dao, sample_account
    ):
        """Test update_account with empty AccountUpdate object"""
        # Arrange
        account_update = AccountUpdate()
        mock_dao.account.update.return_value = sample_account

        # Act
        result = await service.update_account(
            mock_db, mock_dao, sample_account, account_update
        )

        # Assert
        assert result == sample_account
        mock_dao.account.update.assert_called_once_with(
            mock_db, db_obj=sample_account, obj_in=account_update
        )

    @pytest.mark.asyncio
    async def test_get_or_create_account_dao_get_exception(
        self, service, mock_db, mock_dao
    ):
        """Test get_or_create_account when get operation fails"""
        # Arrange
        phone_number = "+1234567890"
        mock_dao.account.get_by_phone_number_without_relations.side_effect = Exception(
            "Get failed"
        )

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await service.get_or_create_account(mock_db, mock_dao, phone_number)

        assert str(exc_info.value) == "Get failed"

    @pytest.mark.asyncio
    async def test_get_or_create_account_dao_create_exception(
        self, service, mock_db, mock_dao
    ):
        """Test get_or_create_account when create operation fails"""
        # Arrange
        phone_number = "+1234567890"
        mock_dao.account.get_by_phone_number_without_relations.return_value = None
        mock_dao.account.create.side_effect = Exception("Create failed")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await service.get_or_create_account(mock_db, mock_dao, phone_number)

        assert str(exc_info.value) == "Create failed"

    @pytest.mark.asyncio
    async def test_update_account_refresh_exception(
        self, service, mock_db, mock_dao, sample_account
    ):
        """Test update_account when db.refresh() raises exception"""
        # Arrange
        account_update = AccountUpdate(email="updated@example.com")
        data = {
            k: v
            for k, v in sample_account.__dict__.items()
            if k != "_sa_instance_state"
        }
        updated_account = Account(**data)
        mock_dao.account.update.return_value = updated_account
        mock_db.refresh.side_effect = Exception("Refresh failed")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await service.update_account(
                mock_db, mock_dao, sample_account, account_update
            )

        assert str(exc_info.value) == "Refresh failed"


# ==================== INTEGRATION-STYLE TESTS ====================


class TestAccountServiceIntegration:
    """Integration-style tests for AccountService workflows"""

    @pytest.fixture
    def service(self):
        return AccountService()

    @pytest.fixture
    def mock_db(self):
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_dao(self):
        dao = MagicMock(spec=HolderDAO)
        dao.account = AsyncMock()
        return dao

    @pytest.mark.asyncio
    async def test_full_account_lifecycle(self, service, mock_db, mock_dao):
        """Test complete account lifecycle: create -> get -> activate -> update"""
        # Arrange
        phone_number = "+1234567890"
        email = "test@example.com"

        # Mock account creation
        created_account = Account(
            id=1,
            phone_number=phone_number,
            email=email,
            is_active=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Mock account retrieval
        data = {
            k: v
            for k, v in created_account.__dict__.items()
            if k != "_sa_instance_state"
        }
        retrieved_account = Account(**data)

        # Mock account update
        updated_account = Account(**data)
        updated_account.email = "updated@example.com"
        updated_account.is_active = True

        mock_dao.account.get_by_phone_number_without_relations.return_value = None
        mock_dao.account.create.return_value = created_account
        mock_dao.account.get.return_value = retrieved_account
        mock_dao.account.update.return_value = updated_account

        # Act & Assert - Create account
        new_account = await service.get_or_create_account(
            mock_db, mock_dao, phone_number
        )
        assert new_account.phone_number == phone_number
        assert new_account.is_active is False

        # Act & Assert - Get account by ID
        fetched_account = await service.get_account_by_id(mock_db, mock_dao, 1)
        assert fetched_account.id == 1

        # Act & Assert - Activate account
        activated_account = await service.set_account_as_active(fetched_account)
        assert activated_account.is_active is True

        # Act & Assert - Update account
        account_update = AccountUpdate(email="updated@example.com")
        final_account = await service.update_account(
            mock_db, mock_dao, activated_account, account_update
        )
        assert final_account.email == "updated@example.com"
