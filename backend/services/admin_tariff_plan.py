from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.holder import HolderDAO
from backend.enums.back_office import TariffStatusEnum
from backend.models.tariff_plan import TariffPlan as TariffPlanModel
from backend.schemas.tariff_plan import TariffPlanCreate


class AdminTariffPlanService:

    async def create_tariff_plan(
        self, session: AsyncSession, dao: HolderDAO, plan_data: TariffPlanCreate
    ) -> TariffPlanModel:
        async with session.begin():
            existing_plan = await dao.tariff_plan.get_by_name(
                session, name=plan_data.name
            )
            if existing_plan:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Tariff plan with name '{plan_data.name}' already exists.",
                )
            if plan_data.is_trial and plan_data.status == TariffStatusEnum.ACTIVE:
                active_trial_plan = await dao.tariff_plan.get_trial_plan(session)
                if active_trial_plan:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"An active trial plan ('{active_trial_plan.name}') already exists.",
                    )
            new_plan = await dao.tariff_plan.create(session, obj_in=plan_data)
            return new_plan
