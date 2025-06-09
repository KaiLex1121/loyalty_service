from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.dao.admin_tarrif_plan import TariffPlanDAO
from backend.dao.holder import HolderDAO
from backend.enums.back_office import CurrencyEnum, PaymentCycleEnum, TariffStatusEnum
from backend.schemas.tariff_plan import TariffPlanCreate
from backend.services.admin_tariff_plan import AdminTariffPlanService


class TestTariffPlanService:

    @pytest.fixture
    def tariff_plan_service(self):
        return AdminTariffPlanService()

    @pytest.fixture
    def mock_tariff_plan_data_base(self):
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

    @pytest.mark.asyncio
    async def test_create_tariff_plan(
        self,
        mock_dao: MagicMock,
        mock_session: AsyncMock,
        tariff_plan_service: AdminTariffPlanService,
        mock_tariff_plan_data_base: TariffPlanCreate,
    ):
        # Arrange
        mock_dao.tariff_plan = MagicMock(spec=TariffPlanDAO)
        mock_dao.tariff_plan.get_by_name = AsyncMock(return_value=None)
        mock_dao.tariff_plan.get_trial_plan = AsyncMock(return_value=None)
        mock_dao.tariff_plan.create.return_value = AsyncMock()
        # Act
        response = await tariff_plan_service.create_tariff_plan(
            mock_session, mock_dao, mock_tariff_plan_data_base
        )

        # Assert
        assert response is not None
