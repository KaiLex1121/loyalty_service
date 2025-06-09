import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dateutil.relativedelta import relativedelta
from fastapi import HTTPException, status
from pydantic import ValidationError

from backend.dao.account import AccountDAO
from backend.dao.admin_tarrif_plan import TariffPlanDAO
from backend.dao.cashback import CashbackConfigDAO
from backend.dao.company import CompanyDAO
from backend.dao.holder import HolderDAO
from backend.dao.subscription import SubscriptionDAO
from backend.dao.user_role import UserRoleDAO
from backend.enums.back_office import (
    CompanyStatusEnum,
    SubscriptionStatusEnum,
    UserAccessLevelEnum,
)
from backend.models.account import Account as AccountModel
from backend.models.company import Company as CompanyModel
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
        dao.account = AsyncMock(spec=AccountDAO)
        dao.user_role = AsyncMock(spec=UserRoleDAO)
        dao.company = AsyncMock(spec=CompanyDAO)
        dao.cashback_config = AsyncMock(spec=CashbackConfigDAO)
        dao.tariff_plan = AsyncMock(spec=TariffPlanDAO)
        dao.subscription = AsyncMock(spec=SubscriptionDAO)
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
        company_service: CompanyService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
        company_data: CompanyCreateRequest,
        mock_account: MagicMock,
        mock_user_role: MagicMock,
        mock_company: MagicMock,
        mock_tariff_plan: MagicMock,
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
        mock_dao.user_role.create.assert_not_called()
        mock_dao.company.create_company_with_owner.assert_called_once()
        mock_dao.cashback_config.create.assert_called_once()
        mock_dao.tariff_plan.get_trial_plan.assert_called_once()
        mock_dao.subscription.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_company_flow_success_with_new_user_role(
        self,
        company_service: CompanyService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
        company_data: CompanyCreateRequest,
        mock_account: MagicMock,
        mock_user_role: MagicMock,
        mock_company: MagicMock,
        mock_tariff_plan: MagicMock,
    ):
        """Тест успешного создания компании с созданием новой пользовательской роли"""
        # Arrange
        account_id = 1
        mock_account.user_profile = None  # Нет существующей роли

        mock_dao.account.get_by_id_with_profiles.return_value = mock_account
        mock_dao.user_role.create.return_value = mock_user_role
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
        mock_dao.user_role.create.assert_called_once()
        mock_dao.company.create_company_with_owner.assert_called_once()

    @pytest.mark.asyncio
    @patch("backend.services.company.datetime")
    async def test_create_company_flow_subscription_dates_calculation(
        self,
        mock_datetime,
        company_service: CompanyService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
        company_data: CompanyCreateRequest,
        mock_account: MagicMock,
        mock_user_role: MagicMock,
        mock_company: MagicMock,
        mock_tariff_plan: MagicMock,
    ):
        """Тест правильного расчета дат подписки"""
        # Arrange
        test_date = datetime.date(2024, 1, 15)
        mock_datetime.date.today.return_value = test_date
        expected_trial_end = test_date + relativedelta(months=3)

        account_id = 1
        mock_account.user_profile = mock_user_role

        mock_dao.account.get_by_id_with_profiles.return_value = mock_account
        mock_dao.company.create_company_with_owner.return_value = mock_company
        mock_dao.cashback_config.create.return_value = AsyncMock()
        mock_dao.tariff_plan.get_trial_plan.return_value = mock_tariff_plan
        mock_dao.subscription.create.return_value = AsyncMock()
        mock_dao.company.get_by_id_with_relations.return_value = mock_company

        # Act
        await company_service.create_company_flow(
            mock_session, mock_dao, company_data, account_id
        )

        # Assert
        subscription_call_args = mock_dao.subscription.create.call_args[1]["obj_in"]
        assert subscription_call_args.start_date == test_date
        assert subscription_call_args.trial_end_date == expected_trial_end
        assert subscription_call_args.next_billing_date == expected_trial_end
        assert subscription_call_args.status == SubscriptionStatusEnum.TRIALING
        assert subscription_call_args.auto_renew is False

    # НЕГАТИВНЫЕ ТЕСТЫ

    @pytest.mark.asyncio
    async def test_create_company_flow_account_not_found(
        self,
        company_service: CompanyService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
        company_data: CompanyCreateRequest,
    ):
        """Тест с несуществующим аккаунтом"""
        # Arrange
        account_id = 999
        mock_dao.account.get_by_id_with_profiles.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await company_service.create_company_flow(
                mock_session, mock_dao, company_data, account_id
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid or inactive account" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_company_flow_inactive_account(
        self,
        company_service: CompanyService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
        company_data: CompanyCreateRequest,
        mock_account: MagicMock,
    ):
        """Тест с неактивным аккаунтом"""
        # Arrange
        account_id = 1
        mock_account.is_active = False
        mock_dao.account.get_by_id_with_profiles.return_value = mock_account

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await company_service.create_company_flow(
                mock_session, mock_dao, company_data, account_id
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_create_company_flow_deleted_account(
        self,
        company_service: CompanyService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
        company_data: CompanyCreateRequest,
        mock_account: MagicMock,
    ):
        """Тест с удаленным аккаунтом"""
        # Arrange
        account_id = 1
        mock_account.is_deleted = True
        mock_dao.account.get_by_id_with_profiles.return_value = mock_account

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await company_service.create_company_flow(
                mock_session, mock_dao, company_data, account_id
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_create_company_flow_no_trial_plan(
        self,
        company_service: CompanyService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
        company_data: CompanyCreateRequest,
        mock_account: MagicMock,
        mock_user_role: MagicMock,
        mock_company: MagicMock,
    ):
        """Тест отсутствия триального тарифного плана"""
        # Arrange
        account_id = 1
        mock_account.user_profile = mock_user_role

        mock_dao.account.get_by_id_with_profiles.return_value = mock_account
        mock_dao.company.create_company_with_owner.return_value = mock_company
        mock_dao.cashback_config.create.return_value = AsyncMock()
        mock_dao.tariff_plan.get_trial_plan.return_value = None  # Нет триального плана

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await company_service.create_company_flow(
                mock_session, mock_dao, company_data, account_id
            )

        assert exc_info.value.status_code == 500
        assert "Trial tariff plan not configured" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_company_flow_company_not_retrieved_after_creation(
        self,
        company_service: CompanyService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
        company_data: CompanyCreateRequest,
        mock_account: MagicMock,
        mock_user_role: MagicMock,
        mock_company: MagicMock,
        mock_tariff_plan: MagicMock,
    ):
        """Тест ошибки при получении созданной компании"""
        # Arrange
        account_id = 1
        mock_account.user_profile = mock_user_role

        mock_dao.account.get_by_id_with_profiles.return_value = mock_account
        mock_dao.company.create_company_with_owner.return_value = mock_company
        mock_dao.cashback_config.create.return_value = AsyncMock()
        mock_dao.tariff_plan.get_trial_plan.return_value = mock_tariff_plan
        mock_dao.subscription.create.return_value = AsyncMock()
        mock_dao.company.get_by_id_with_relations.return_value = None  # Не найдена

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await company_service.create_company_flow(
                mock_session, mock_dao, company_data, account_id
            )

        assert exc_info.value.status_code == 500
        assert (
            "Failed to retrieve newly created company details" in exc_info.value.detail
        )

    # ГРАНИЧНЫЕ И КОРНЕР ТЕСТЫ

    @pytest.mark.asyncio
    async def test_create_company_flow_user_role_creation_fails(
        self,
        company_service: CompanyService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
        company_data: CompanyCreateRequest,
        mock_account: MagicMock,
    ):
        """Тест ошибки при создании пользовательской роли"""
        # Arrange
        account_id = 1
        mock_account.user_profile = None

        mock_dao.account.get_by_id_with_profiles.return_value = mock_account
        mock_dao.user_role.create.return_value = None  # Создание не удалось

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await company_service.create_company_flow(
                mock_session, mock_dao, company_data, account_id
            )

        assert "UserRole could not be established" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_company_flow_user_role_without_id(
        self,
        company_service: CompanyService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
        company_data: CompanyCreateRequest,
        mock_account: MagicMock,
    ):
        """Тест пользовательской роли без ID"""
        # Arrange
        account_id = 1
        mock_account.user_profile = None

        mock_user_role_without_id = MagicMock(spec=UserRoleModel)
        mock_user_role_without_id.id = None  # Нет ID

        mock_dao.account.get_by_id_with_profiles.return_value = mock_account
        mock_dao.user_role.create.return_value = mock_user_role_without_id

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await company_service.create_company_flow(
                mock_session, mock_dao, company_data, account_id
            )

        assert "UserRole could not be established" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_company_flow_database_transaction_rollback(
        self,
        company_service: CompanyService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
        company_data: CompanyCreateRequest,
        mock_account: MagicMock,
        mock_user_role: MagicMock,
    ):
        """Тест отката транзакции при ошибке"""
        # Arrange
        account_id = 1
        mock_account.user_profile = mock_user_role

        mock_dao.account.get_by_id_with_profiles.return_value = mock_account
        mock_dao.company.create_company_with_owner.side_effect = Exception(
            "Database error"
        )

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await company_service.create_company_flow(
                mock_session, mock_dao, company_data, account_id
            )

        assert "Database error" in str(exc_info.value)
        # Проверяем, что транзакция была начата
        mock_session.begin.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_company_flow_raises_error_on_zero_cashback(
        self,
    ):  # Название изменено для ясности
        """Тест проверяет, что создание компании с 0% кешбека вызывает ошибку валидации"""
        # Arrange & Act
        with pytest.raises(ValidationError) as exc_info:
            CompanyCreateRequest(
                name="Test Company",
                inn="1234567890",
                initial_cashback_percentage=0.0,  # Невалидное значение
                description="Test company description",
                legal_form="ООО",
                legal_name="Test Legal Name",
            )

        # Assert
        # Можно дополнительно проверить текст ошибки для надежности
        assert "initial_cashback_percentage" in str(exc_info.value)
        assert "Input should be greater than 0" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_company_flow_high_cashback_percentage(
        self,
        company_service: CompanyService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
        mock_account: MagicMock,
        mock_user_role: MagicMock,
        mock_company: MagicMock,
        mock_tariff_plan: MagicMock,
    ):
        """Тест с высоким процентом кешбека"""
        # Arrange
        account_id = 1
        company_data_high_cashback = CompanyCreateRequest(
            name="Test Company",
            inn="1234567890",
            initial_cashback_percentage=99.9,  # Высокий процент
            description="Test company description",
            legal_form="ООО",
            legal_name="Test Legal Name",
        )

        mock_account.user_profile = mock_user_role
        mock_dao.account.get_by_id_with_profiles.return_value = mock_account
        mock_dao.company.create_company_with_owner.return_value = mock_company
        mock_dao.cashback_config.create.return_value = AsyncMock()
        mock_dao.tariff_plan.get_trial_plan.return_value = mock_tariff_plan
        mock_dao.subscription.create.return_value = AsyncMock()
        mock_dao.company.get_by_id_with_relations.return_value = mock_company

        # Act
        result = await company_service.create_company_flow(
            mock_session, mock_dao, company_data_high_cashback, account_id
        )

        # Assert
        assert result == mock_company
        cashback_call_args = mock_dao.cashback_config.create.call_args[1]["obj_in"]
        assert cashback_call_args.default_percentage == Decimal("99.9")


class TestCompanyServiceEdgeCases:

    @pytest.fixture
    def company_service(self):
        return CompanyService()

    @pytest.mark.asyncio
    async def test_create_company_flow_with_minimal_data(
        self, company_service: CompanyService, mock_session: AsyncMock
    ):
        """Тест с минимальным набором данных"""
        # Arrange
        mock_dao = MagicMock()

        minimal_company_data = CompanyCreateRequest(
            name="A",  # Минимальное имя
            inn="1234567890",
            initial_cashback_percentage=0.01,  # Минимальный процент
            legal_form="ООО",
            legal_name="Test Legal Name",
        )

        # Настройка моков для успешного выполнения
        mock_account = MagicMock()
        mock_account.is_active = True
        mock_account.is_deleted = False
        mock_user_role = MagicMock()
        mock_user_role.id = 1
        mock_account.user_profile = mock_user_role

        mock_company = MagicMock()
        mock_company.id = 1

        mock_tariff_plan = MagicMock()
        mock_tariff_plan.id = 1

        mock_dao.account.get_by_id_with_profiles = AsyncMock(return_value=mock_account)
        mock_dao.company.create_company_with_owner = AsyncMock(
            return_value=mock_company
        )
        mock_dao.cashback_config.create = AsyncMock()
        mock_dao.tariff_plan.get_trial_plan = AsyncMock(return_value=mock_tariff_plan)
        mock_dao.subscription.create = AsyncMock()
        mock_dao.company.get_by_id_with_relations = AsyncMock(return_value=mock_company)

        # Act
        result = await company_service.create_company_flow(
            mock_session, mock_dao, minimal_company_data, 1
        )

        # Assert
        assert result == mock_company

    @pytest.mark.asyncio
    async def test_create_company_flow_transaction_context_manager(
        self, company_service: CompanyService, mock_session: AsyncMock
    ):
        """Тест корректной работы контекстного менеджера транзакции"""
        # Arrange
        mock_dao = MagicMock()
        company_data = CompanyCreateRequest(
            name="Test Company",
            inn="1234567890",
            initial_cashback_percentage=5.0,
            legal_form="ООО",
            legal_name="Test Legal Name",
        )

        # Настройка для успешного выполнения
        mock_account = MagicMock()
        mock_account.is_active = True
        mock_account.is_deleted = False
        mock_user_role = MagicMock()
        mock_user_role.id = 1
        mock_account.user_profile = mock_user_role

        mock_company = MagicMock()
        mock_company.id = 1

        mock_tariff_plan = MagicMock()
        mock_tariff_plan.id = 1

        mock_dao.account.get_by_id_with_profiles = AsyncMock(return_value=mock_account)
        mock_dao.company.create_company_with_owner = AsyncMock(
            return_value=mock_company
        )
        mock_dao.cashback_config.create = AsyncMock()
        mock_dao.tariff_plan.get_trial_plan = AsyncMock(return_value=mock_tariff_plan)
        mock_dao.subscription.create = AsyncMock()
        mock_dao.company.get_by_id_with_relations = AsyncMock(return_value=mock_company)

        # Act
        await company_service.create_company_flow(
            mock_session, mock_dao, company_data, 1
        )

        # Assert
        mock_session.begin.assert_called_once()
