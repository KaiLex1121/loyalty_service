from app.dao.holder import HolderDAO
from app.enums import TariffStatusEnum
from app.exceptions.services.tariff_plan import (
    TariffPlanNameConflictException,
)
from app.models.tariff_plan import (
    TariffPlan as TariffPlanModel,  # Не используется напрямую, но для контекста
)
from app.schemas.company_tariff_plan import TariffPlanCreate, TariffPlanResponse
from sqlalchemy.ext.asyncio import AsyncSession


class AdminTariffPlanService:

    async def create_tariff_plan(
        self, session: AsyncSession, dao: HolderDAO, plan_data: TariffPlanCreate
    ) -> TariffPlanResponse:

        existing_plan_by_name = await dao.tariff_plan.get_by_name(
            session, name=plan_data.name
        )
        if existing_plan_by_name:
            raise TariffPlanNameConflictException(name=plan_data.name)

        new_plan = await dao.tariff_plan.create(session, obj_in=plan_data)

        return TariffPlanResponse.model_validate(new_plan)
