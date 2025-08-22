import datetime
import time
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from venv import create

import pytest
from app.dao.admin_tariff_plan import TariffPlanDAO
from app.enums.back_office import CurrencyEnum, PaymentCycleEnum, TariffStatusEnum
from app.models.tariff_plan import TariffPlan as TariffPlanModel
from app.schemas.company_tariff_plan import TariffPlanCreate, TariffPlanResponse
from app.services.company_tariff_plan import AdminTariffPlanService
from fastapi import HTTPException, status
from pydantic import ValidationError


class TestTariffPlanService:

    @pytest.fixture
    def tariff_plan_service(self) -> AdminTariffPlanService:
        return AdminTariffPlanService()

    @pytest.fixture
    def tariff_plan_data(self) -> TariffPlanCreate:
        return TariffPlanCreate(
            name="Test Tariff Plan",
            description="Test description",
            price=Decimal("100.00"),
            currency=CurrencyEnum.RUB,
            billing_period=PaymentCycleEnum.MONTHLY,
            max_outlets=5,
            max_employees=10,
            max_active_promotions=2,
            features=["feature1", "feature2"],
            status=TariffStatusEnum.ACTIVE,
            is_public=True,
            is_trial=False,
            trial_duration_days=None,
            sort_order=0,
        )

    @pytest.fixture
    def trial_tariff_plan_data(self) -> TariffPlanCreate:
        return TariffPlanCreate(
            name="Test Tariff Plan",
            description="Test description",
            price=Decimal("0.00"),
            currency=CurrencyEnum.RUB,
            billing_period=PaymentCycleEnum.MONTHLY,
            max_outlets=5,
            max_employees=10,
            max_active_promotions=2,
            features=["feature1", "feature2"],
            status=TariffStatusEnum.ACTIVE,
            is_public=True,
            is_trial=True,
            trial_duration_days=30,
            sort_order=0,
        )

    @pytest.fixture
    def tariff_plan_model(self):
        return TariffPlanModel(
            id=1,
            name="Test Tariff Plan",
            description="Test description",
            price=Decimal("123"),
            currency=CurrencyEnum.RUB,
            billing_period=PaymentCycleEnum.MONTHLY,
            max_outlets=5,
            max_employees=10,
            max_active_promotions=2,
            features=["feature1", "feature2"],
            status=TariffStatusEnum.ACTIVE,
            is_public=True,
            is_trial=True,
            trial_duration_days=30,
            sort_order=0,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )

    # POSITIVE TESTS
    @pytest.mark.asyncio
    async def test_create_tariff_plan_success(
        self,
        tariff_plan_service: AdminTariffPlanService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
        tariff_plan_data: TariffPlanCreate,
        tariff_plan_model: TariffPlanModel,
    ):
        """Test successful creation of a regular tariff plan."""
        # Arrange
        mock_dao.tariff_plan = AsyncMock(spec=TariffPlanDAO)
        mock_dao.tariff_plan.get_by_name = AsyncMock(return_value=None)
        mock_dao.tariff_plan.create = AsyncMock(return_value=tariff_plan_model)

        # Act
        result = await tariff_plan_service.create_tariff_plan(
            session=mock_session, dao=mock_dao, plan_data=tariff_plan_data
        )

        # Assert
        assert isinstance(result, TariffPlanResponse)
        assert result.id == tariff_plan_model.id
        assert result.name == tariff_plan_model.name
        assert result.description == tariff_plan_model.description
        assert result.price == tariff_plan_model.price
        assert result.is_trial == tariff_plan_model.is_trial
        assert result.status == tariff_plan_model.status
        # добавьте другие важные поля

        mock_dao.tariff_plan.get_by_name.assert_called_once_with(
            mock_session, name=tariff_plan_data.name
        )
        mock_dao.tariff_plan.create.assert_called_once_with(
            mock_session, obj_in=tariff_plan_data
        )

    @pytest.mark.asyncio
    async def test_create_trial_plan_success_no_existing_trial(
        self,
        tariff_plan_service: AdminTariffPlanService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
        trial_tariff_plan_data: TariffPlanCreate,
    ):
        """Test successful creation of trial plan when no active trial exists"""
        # Arrange
        trial_plan_model = TariffPlanModel(
            id=2,
            name="Test Trial Plan",
            description="Test description",
            price=Decimal("0.00"),
            currency=CurrencyEnum.RUB,
            billing_period=PaymentCycleEnum.MONTHLY,
            max_outlets=5,
            max_employees=10,
            max_active_promotions=2,
            features=["feature1", "feature2"],
            status=TariffStatusEnum.ACTIVE,
            is_public=True,
            is_trial=True,
            trial_duration_days=30,
            sort_order=0,
        )
        mock_dao.tariff_plan = AsyncMock(spec=TariffPlanDAO)
        mock_dao.tariff_plan.get_by_name = AsyncMock(return_value=None)
        mock_dao.tariff_plan.get_trial_plan = AsyncMock(return_value=None)
        mock_dao.tariff_plan.create = AsyncMock(return_value=trial_plan_model)

        # Act
        result = await tariff_plan_service.create_tariff_plan(
            mock_session, mock_dao, trial_tariff_plan_data
        )

        # Assert
        assert result == trial_plan_model
        mock_dao.tariff_plan.get_by_name.assert_called_once_with(
            mock_session, name=trial_tariff_plan_data.name
        )
        mock_dao.tariff_plan.get_trial_plan.assert_called_once_with(mock_session)
        mock_dao.tariff_plan.create.assert_called_once_with(
            mock_session, obj_in=trial_tariff_plan_data
        )

    @pytest.mark.asyncio
    async def test_create_inactive_trial_plan_success(
        self,
        tariff_plan_service: AdminTariffPlanService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
    ):
        """Test successful creation of hidden trial plan even when active trial exists"""
        # Arrange
        hidden_trial_data = TariffPlanCreate(
            name="Hidden Trial",
            description="Hidden trial",
            price=Decimal("0.00"),
            currency=CurrencyEnum.RUB,
            billing_period=PaymentCycleEnum.MONTHLY,
            max_outlets=5,
            max_employees=10,
            max_active_promotions=2,
            features=["feature1", "feature2"],
            status=TariffStatusEnum.HIDDEN,
            is_public=True,
            is_trial=True,
            trial_duration_days=30,
            sort_order=0,
        )
        hidden_trial_model = TariffPlanModel(
            id=3,
            name="Hidden Trial",
            description="Hidden trial",
            price=Decimal("0.00"),
            currency=CurrencyEnum.RUB,
            billing_period=PaymentCycleEnum.MONTHLY,
            max_outlets=5,
            max_employees=10,
            max_active_promotions=2,
            features=["feature1", "feature2"],
            status=TariffStatusEnum.HIDDEN,
            is_public=True,
            is_trial=True,
            trial_duration_days=30,
            sort_order=0,
        )

        mock_dao.tariff_plan = AsyncMock(spec=TariffPlanDAO)
        mock_dao.tariff_plan.get_by_name = AsyncMock(return_value=None)
        mock_dao.tariff_plan.create = AsyncMock(return_value=hidden_trial_model)

        # Act
        result = await tariff_plan_service.create_tariff_plan(
            mock_session, mock_dao, hidden_trial_data
        )

        # Assert
        assert result == hidden_trial_model
        # get_trial_plan should not be called for hidden trials
        mock_dao.tariff_plan.get_trial_plan.assert_not_called()

    # NEGATIVE TEST CASES
    @pytest.mark.asyncio
    async def test_create_tariff_plan_duplicate_name(
        self,
        tariff_plan_service: AdminTariffPlanService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
        tariff_plan_data: TariffPlanCreate,
        tariff_plan_model: TariffPlanModel,
    ):
        """Test creation fails when plan with same name already exists"""
        # Arrange
        mock_dao.tariff_plan = AsyncMock(spec=TariffPlanDAO)
        mock_dao.tariff_plan.get_by_name = AsyncMock(return_value=tariff_plan_model)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await tariff_plan_service.create_tariff_plan(
                mock_session, mock_dao, tariff_plan_data
            )

        # Проверяем, что исключение имеет правильные параметры
        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert (
            f"Tariff plan with name '{tariff_plan_data.name}' already exists."
            in str(exc_info.value.detail)
        )

        # Проверяем, что create не был вызван
        mock_dao.tariff_plan.create.assert_not_called()

        # Проверяем, что get_by_name был вызван с правильными параметрами
        mock_dao.tariff_plan.get_by_name.assert_called_once_with(
            mock_session, name=tariff_plan_data.name
        )

    @pytest.mark.asyncio
    async def test_create_active_trial_plan_when_trial_exists(
        self,
        tariff_plan_service: AdminTariffPlanService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
        trial_tariff_plan_data: TariffPlanCreate,
    ):
        """Test creation fails when trying to create active trial plan while another active trial exists"""
        # Arrange
        existing_trial = TariffPlanModel(
            id=4,
            name="Existing Trial",
            description="Existing trial",
            price=Decimal("0.00"),
            currency=CurrencyEnum.RUB,
            billing_period=PaymentCycleEnum.MONTHLY,
            max_outlets=5,
            max_employees=10,
            max_active_promotions=2,
            features=["feature1", "feature2"],
            status=TariffStatusEnum.ACTIVE,
            is_public=True,
            is_trial=True,
            trial_duration_days=30,
            sort_order=0,
        )
        mock_dao.tariff_plan = AsyncMock(spec=TariffPlanDAO)
        mock_dao.tariff_plan.get_by_name.return_value = None
        mock_dao.tariff_plan.get_trial_plan.return_value = existing_trial

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await tariff_plan_service.create_tariff_plan(
                mock_session, mock_dao, trial_tariff_plan_data
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert f"An active trial plan ('{existing_trial.name}') already exists." in str(
            exc_info.value.detail
        )
        mock_dao.tariff_plan.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_database_error_during_creation(
        self,
        tariff_plan_service: AdminTariffPlanService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
        tariff_plan_data: TariffPlanCreate,
    ):
        """Test handling of database errors during plan creation"""
        # Arrange
        mock_dao.tariff_plan = AsyncMock(spec=TariffPlanDAO)
        mock_dao.tariff_plan.get_by_name.return_value = None
        mock_dao.tariff_plan.create.side_effect = Exception("Database connection error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await tariff_plan_service.create_tariff_plan(
                mock_session, mock_dao, tariff_plan_data
            )

        assert "Database connection error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_database_error_during_name_check(
        self,
        tariff_plan_service: AdminTariffPlanService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
        tariff_plan_data: TariffPlanCreate,
    ):
        """Test handling of database errors during name existence check"""
        # Arrange
        mock_dao.tariff_plan = AsyncMock(spec=TariffPlanDAO)
        mock_dao.tariff_plan.get_by_name.side_effect = Exception("Database query error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await tariff_plan_service.create_tariff_plan(
                mock_session, mock_dao, tariff_plan_data
            )

        assert "Database query error" in str(exc_info.value)
        mock_dao.tariff_plan.create.assert_not_called()

    # CORNER CASES / EDGE CASES
    @pytest.mark.asyncio
    async def test_create_plan_with_empty_name(self, mock_dao: MagicMock):
        """Test creation with empty name should raise validation error"""
        # Arrange
        mock_dao.tariff_plan = AsyncMock(spec=TariffPlanDAO)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            empty_name_data = TariffPlanCreate(
                name="",
                description="Empty name plan",
                price=Decimal("50.00"),
                currency=CurrencyEnum.RUB,
                billing_period=PaymentCycleEnum.MONTHLY,
                max_outlets=5,
                max_employees=10,
                max_active_promotions=2,
                features=["feature1", "feature2"],
                status=TariffStatusEnum.ACTIVE,
                is_public=True,
                is_trial=False,
                trial_duration_days=None,
                sort_order=0,
            )

        # Проверяем, что ошибка именно о коротком имени
        assert "String should have at least 3 characters" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_plan_with_special_characters_in_name(
        self,
        tariff_plan_service: AdminTariffPlanService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
    ):
        """Test creation with special characters in name"""
        # Arrange
        special_name_data = TariffPlanCreate(
            name="Plan@#$%^&*()_+-={}[]|\\:;\"'<>?,./ ",
            description="Special chars plan",
            price=Decimal("75.00"),
            currency=CurrencyEnum.RUB,
            billing_period=PaymentCycleEnum.MONTHLY,
            max_outlets=5,
            max_employees=10,
            max_active_promotions=2,
            features=["feature1", "feature2"],
            status=TariffStatusEnum.ACTIVE,
            is_public=True,
            is_trial=False,
            trial_duration_days=None,
            sort_order=0,
        )
        created_plan = TariffPlanModel(
            id=6,
            name="Plan@#$%^&*()_+-={}[]|\\:;\"'<>?,./ ",
            description="Special chars plan",
            price=Decimal("75.00"),
            currency=CurrencyEnum.RUB,
            billing_period=PaymentCycleEnum.MONTHLY,
            max_outlets=5,
            max_employees=10,
            max_active_promotions=2,
            features=["feature1", "feature2"],
            status=TariffStatusEnum.ACTIVE,
            is_public=True,
            is_trial=False,
            trial_duration_days=None,
            sort_order=0,
        )

        mock_dao.tariff_plan = AsyncMock(spec=TariffPlanDAO)
        mock_dao.tariff_plan.get_by_name = AsyncMock(return_value=None)
        mock_dao.tariff_plan.create = AsyncMock(return_value=created_plan)

        # Act
        result = await tariff_plan_service.create_tariff_plan(
            mock_session, mock_dao, special_name_data
        )

        # Assert
        assert result == created_plan

    @pytest.mark.asyncio
    async def test_create_plan_with_zero_price(
        self,
        tariff_plan_service: AdminTariffPlanService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
    ):
        """Test creation with zero price (but not trial)"""
        # Arrange
        zero_price_data = TariffPlanCreate(
            name="Free Plan",
            description="Free tier",
            price=Decimal("0.00"),
            currency=CurrencyEnum.RUB,
            billing_period=PaymentCycleEnum.MONTHLY,
            max_outlets=5,
            max_employees=10,
            max_active_promotions=2,
            features=["feature1", "feature2"],
            status=TariffStatusEnum.ACTIVE,
            is_public=True,
            is_trial=False,
            trial_duration_days=None,
            sort_order=0,
        )
        created_plan = TariffPlanModel(
            id=7,
            name="Free Plan",
            description="Free tier",
            price=Decimal("0.00"),
            currency=CurrencyEnum.RUB,
            billing_period=PaymentCycleEnum.MONTHLY,
            max_outlets=5,
            max_employees=10,
            max_active_promotions=2,
            features=["feature1", "feature2"],
            status=TariffStatusEnum.ACTIVE,
            is_public=True,
            is_trial=False,
            trial_duration_days=None,
            sort_order=0,
        )
        mock_dao.tariff_plan = AsyncMock(spec=TariffPlanDAO)
        mock_dao.tariff_plan.create = AsyncMock(return_value=created_plan)
        mock_dao.tariff_plan.get_by_name = AsyncMock(return_value=None)

        # Act
        result = await tariff_plan_service.create_tariff_plan(
            mock_session, mock_dao, zero_price_data
        )

        # Assert
        assert result == created_plan
        # Should not check for existing trial plans since is_trial=False
        mock_dao.tariff_plan.get_trial_plan.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_plan_with_very_long_name(
        self,
        tariff_plan_service: AdminTariffPlanService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
    ):
        """Test creation with very long name should fail validation"""
        # Arrange
        long_name = "A" * 101  # Превышает лимит в 100 символов

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TariffPlanCreate(
                name=long_name,
                description="Long name plan",
                price=100.00,
                is_trial=False,
                status=TariffStatusEnum.ACTIVE,
            )

        # Проверяем, что ошибка именно о длине строки
        assert "string_too_long" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_session_transaction_behavior(
        self,
        tariff_plan_service: AdminTariffPlanService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
        tariff_plan_data: TariffPlanCreate,
        tariff_plan_model: TariffPlanModel,
    ):
        """Test that session.begin() is properly used for transaction management"""
        # Arrange
        mock_dao.tariff_plan = AsyncMock(spec=TariffPlanDAO)
        mock_dao.tariff_plan.get_by_name = AsyncMock(return_value=None)
        mock_dao.tariff_plan.create = AsyncMock(return_value=tariff_plan_model)

        # Act
        await tariff_plan_service.create_tariff_plan(
            mock_session, mock_dao, tariff_plan_data
        )

        # Assert
        mock_session.begin.assert_called_once()

    @pytest.mark.asyncio
    async def test_case_sensitive_name_comparison(
        self,
        tariff_plan_service: AdminTariffPlanService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
    ):
        """Test that name comparison is case-sensitive (assuming DAO handles this)"""
        # Arrange
        uppercase_data = TariffPlanCreate(
            name="PREMIUM PLAN",
            description="Uppercase plan",
            price=99.99,
            is_trial=False,
            status=TariffStatusEnum.ACTIVE,
        )
        created_plan = TariffPlanModel(
            id=9,
            name="PREMIUM PLAN",
            description="Uppercase plan",
            price=99.99,
            is_trial=False,
            status=TariffStatusEnum.ACTIVE,
        )
        mock_dao.tariff_plan = AsyncMock(spec=TariffPlanDAO)
        mock_dao.tariff_plan.get_by_name = AsyncMock(return_value=None)
        mock_dao.tariff_plan.create = AsyncMock(return_value=created_plan)

        # Act
        result = await tariff_plan_service.create_tariff_plan(
            mock_session, mock_dao, uppercase_data
        )

        # Assert
        assert result == created_plan
        mock_dao.tariff_plan.get_by_name.assert_called_once_with(
            mock_session, name="PREMIUM PLAN"
        )

    @pytest.mark.asyncio
    async def test_trial_plan_status_combinations(
        self,
        tariff_plan_service: AdminTariffPlanService,
        mock_session: AsyncMock,
        mock_dao: MagicMock,
    ):
        """Test various combinations of trial flag and status"""
        test_cases = [
            # (is_trial, status, should_check_existing_trial)
            (True, TariffStatusEnum.ACTIVE, True),
            (True, TariffStatusEnum.HIDDEN, False),
            (False, TariffStatusEnum.ACTIVE, False),
            (False, TariffStatusEnum.HIDDEN, False),
        ]

        for i, (is_trial, status, should_check_trial) in enumerate(test_cases):
            # Reset mocks
            mock_dao.reset_mock()

            # Arrange
            plan_data = TariffPlanCreate(
                name=f"Test Plan {i}",
                description=f"Test plan {i}",
                price=10.00 * i,
                is_trial=is_trial,
                status=status,
            )
            created_plan = TariffPlanModel(
                id=10 + i,
                name=f"Test Plan {i}",
                description=f"Test plan {i}",
                price=10.00 * i,
                is_trial=is_trial,
                status=status,
            )
            mock_dao.tariff_plan = AsyncMock(spec=TariffPlanDAO)
            mock_dao.tariff_plan.get_by_name = AsyncMock(return_value=None)
            mock_dao.tariff_plan.get_trial_plan = AsyncMock(return_value=None)
            mock_dao.tariff_plan.create = AsyncMock(return_value=created_plan)

            # Act
            result = await tariff_plan_service.create_tariff_plan(
                mock_session, mock_dao, plan_data
            )

            # Assert
            assert result == created_plan
            if should_check_trial:
                mock_dao.tariff_plan.get_trial_plan.assert_called_once_with(
                    mock_session
                )
            else:
                mock_dao.tariff_plan.get_trial_plan.assert_not_called()
