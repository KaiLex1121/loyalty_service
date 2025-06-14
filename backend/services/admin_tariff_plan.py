from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.holder import HolderDAO
from backend.enums.back_office import TariffStatusEnum
from backend.exceptions.services.tarrif_plan import (
    ActiveTrialPlanConflictException,
    TariffPlanNameConflictException,
)
from backend.models.tariff_plan import (
    TariffPlan as TariffPlanModel,  # Не используется напрямую, но для контекста
)
from backend.schemas.tariff_plan import TariffPlanCreate, TariffPlanResponse


class AdminTariffPlanService:

    async def create_tariff_plan(
        self, session: AsyncSession, dao: HolderDAO, plan_data: TariffPlanCreate
    ) -> TariffPlanResponse:
        async with session.begin():
            existing_plan_by_name = await dao.tariff_plan.get_by_name(
                session, name=plan_data.name
            )
            if existing_plan_by_name:
                raise TariffPlanNameConflictException(name=plan_data.name)

            if plan_data.is_trial and plan_data.status == TariffStatusEnum.ACTIVE:
                active_trial_plan = await dao.tariff_plan.get_trial_plan(session)
                # Убедимся, что get_trial_plan возвращает только активные или проверяем статус здесь
                # Предположим, get_trial_plan возвращает активный триальный план, если он есть
                if (
                    active_trial_plan
                    and active_trial_plan.status == TariffStatusEnum.ACTIVE
                ):
                    # Проверяем, что это не тот же самый план, который мы пытаемся обновить (если бы это был update)
                    # Для create это всегда будет другой план
                    raise ActiveTrialPlanConflictException(
                        existing_plan_name=active_trial_plan.name,
                        internal_details={
                            "attempted_plan_name": plan_data.name,
                            "existing_plan_id": active_trial_plan.id,
                        },
                    )
            new_plan = await dao.tariff_plan.create(session, obj_in=plan_data)

        # Валидация ответа. Если здесь будет ValidationError, ее поймает pydantic_validation_error_handler
        # и вернет 500, что корректно.
        return TariffPlanResponse.model_validate(new_plan)
