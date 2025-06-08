import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dateutil.relativedelta import relativedelta
from fastapi import HTTPException, status

from backend.dao.holder import HolderDAO
from backend.enums.back_office import (CompanyStatusEnum,
                                       SubscriptionStatusEnum,
                                       UserAccessLevelEnum)
from backend.models.account import Account as AccountModel
from backend.models.company import Company as CompanyModel
from backend.models.subscription import Subscription as SubscriptionModel
from backend.models.tariff_plan import TariffPlan as TariffPlanModel
from backend.models.user_role import UserRole as UserRoleModel
from backend.schemas.company import CompanyCreateRequest
from backend.services.company import CompanyService


class TestCompanyService:
    """Тестовый класс для CompanyService"""

    @pytest.fixture
    def company_service(self):
        """Фикстура для создания экземпляра CompanyService"""
        return CompanyService()

    @pytest.fixture
    def mock_dao(self):
        """Мок для HolderDAO"""
        dao = MagicMock(spec=HolderDAO)
        dao.account = AsyncMock()
        dao.user_role = AsyncMock()
        dao.company = AsyncMock()
        dao.cashback_config = AsyncMock()
        dao.tariff_plan = AsyncMock()
        dao.subscription = AsyncMock()
        return dao

    @pytest.fixture
    def company_data(self):
        """Фикстура для данных компании"""
        return CompanyCreateRequest(
            name="Test Company",
            inn="1234567890",
            initial_cashback_percentage=5.0,
            description="Test company description",
            legal_form="ООО",
            legal_name="Test Legal Name",
        )

    @pytest.fixture
    def mock_account(self):
        """Мок для аккаунта"""
        account = MagicMock(spec=AccountModel)
        account.id = 1
        account.is_active = True
        account.is_deleted = False
        account.user_profile = None
        return account

    @pytest.fixture
    def mock_user_role(self):
        """Мок для пользовательской роли"""
        user_role = MagicMock(spec=UserRoleModel)
        user_role.id = 1
        user_role.access_level = UserAccessLevelEnum.COMPANY_OWNER
        return user_role

    @pytest.fixture
    def mock_company(self):
        """Мок для компании"""
        company = MagicMock(spec=CompanyModel)
        company.id = 1
        company.name = "Test Company"
        company.status = CompanyStatusEnum.PENDING_VERIFICATION
        return company

    @pytest.fixture
    def mock_tariff_plan(self):
        """Мок для тарифного плана"""
        tariff_plan = MagicMock(spec=TariffPlanModel)
        tariff_plan.id = 1
        tariff_plan.name = "Trial Plan"
        tariff_plan.is_trial = True
        return tariff_plan

    # ПОЗИТИВНЫЕ ТЕСТЫ

    @pytest.mark.asyncio
    async def test_create_company_flow_success_with_existing_user_role(
        self,
        company_service,
        mock_session,
        mock_dao,
        company_data,
        mock_account,
        mock_user_role,
        mock_company,
        mock_tariff_plan,
    ):
        """Тест успешного создания компании с существующей пользовательской ролью"""
        # Arrange
        account_id = 1
        mock_account.user_profile = mock_user_role

        mock_dao.account.get_by_id_with_profiles.return_value = mock_account
        mock_dao.company.create_company_with_owner.return_value = mock_company
        mock_dao.cashback_config.create.return_value = AsyncMock()
        mock_dao.tariff_plan.get_trial_plan.return_value = mock_tariff_plan
        mock_dao.subscription.create.return_value = AsyncMock()
        mock_dao.company.get_by_id_with_relations.return_value = mock_company

        # Act
        result = await company_service.create_company_flow(
            mock_session, mock_dao, company_data, account_id
        )

        # Assert
        assert result == mock_company
        mock_dao.account.get_by_id_with_profiles.assert_called_once_with(
            mock_session, id_=account_id
        )
        mock_dao.user_role.create.assert_not_called()  # Не создаем новую роль
        mock_dao.company.create_company_with_owner.assert_called_once()
        mock_dao.cashback_config.create.assert_called_once()
        mock_dao.tariff_plan.get_trial_plan.assert_called_once()
        mock_dao.subscription.create.assert_called_once()
