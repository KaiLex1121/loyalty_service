from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select  # Для явного SELECT с options

from backend.dao.holder import \
    HolderDAO  # Предполагаем, что HolderDAO принимает сессию при инициализации или DAO получают сессию в методах
from backend.enums.back_office import TariffStatusEnum
from backend.models.tariff_plan import TariffPlan as TariffPlanModel
from backend.schemas.tariff_plan import (TariffPlanCreate, TariffPlanResponse,
                                         TariffPlanUpdate)


class AdminTariffPlanService:
    async def _load_plan_for_response(
        self, session: AsyncSession, dao: HolderDAO, plan_id: int
    ) -> Optional[TariffPlanModel]:
        # Вспомогательный метод для загрузки плана (если нужны связи для ответа)
        # В данном случае TariffPlanResponse простая, так что можно обойтись без него
        # или использовать dao.tariff_plan.get(session, id_=plan_id)
        return await dao.tariff_plan.get(session, id_=plan_id)

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

    async def get_tariff_plan(
        self, session: AsyncSession, dao: HolderDAO, plan_id: int
    ) -> Optional[TariffPlanModel]:
        # Для GET операций явный session.begin() не всегда нужен, если сессия настроена на autocommit=False
        # и мы не делаем несколько последовательных чтений, требующих одного снимка данных.
        # Но для консистентности можно и GET обернуть, если есть вероятность изменений другими запросами.
        # В данном случае, простой get из DAO должен быть достаточен.
        return await dao.tariff_plan.get(session, id_=plan_id)

    async def get_all_tariff_plans(
        self, session: AsyncSession, dao: HolderDAO, skip: int = 0, limit: int = 100
    ) -> List[TariffPlanModel]:
        return await dao.tariff_plan.get_multi(
            session, skip=skip, limit=limit, include_deleted=True
        )

    async def update_tariff_plan(
        self,
        session: AsyncSession,
        dao: HolderDAO,
        plan_id: int,
        plan_update_data: TariffPlanUpdate,
    ) -> Optional[TariffPlanModel]:
        async with session.begin():  # <--- ТРАНЗАКЦИЯ ЗДЕСЬ
            plan_to_update = await dao.tariff_plan.get(session, id_=plan_id)
            if not plan_to_update:
                return None  # Или выбросить HTTPException(404)

            if plan_update_data.name and plan_update_data.name != plan_to_update.name:
                # ... (проверка уникальности имени) ...
                existing_plan_with_new_name = await dao.tariff_plan.get_by_name(
                    session, name=plan_update_data.name
                )
                if (
                    existing_plan_with_new_name
                    and existing_plan_with_new_name.id != plan_id
                ):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Tariff plan with name '{plan_update_data.name}' already exists.",
                    )

            if (
                plan_update_data.is_trial is not None
                and plan_update_data.is_trial
                and (
                    plan_update_data.status == TariffStatusEnum.ACTIVE
                    if plan_update_data.status
                    else plan_to_update.status == TariffStatusEnum.ACTIVE
                )
            ):
                # ... (проверка на другой активный триал) ...
                active_trial_plan = await dao.tariff_plan.get_trial_plan(session)
                if active_trial_plan and active_trial_plan.id != plan_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="An active trial plan already exists.",
                    )

            # dao.tariff_plan.update НЕ должен делать commit
            updated_plan = await dao.tariff_plan.update(
                session, db_obj=plan_to_update, obj_in=plan_update_data
            )
            # await session.refresh(updated_plan) # Если update не делает refresh
            return updated_plan

    async def archive_tariff_plan(  # Переименовали из delete_tariff_plan
        self, session: AsyncSession, dao: HolderDAO, plan_id: int
    ) -> Optional[TariffPlanModel]:
        async with session.begin():  # <--- ТРАНЗАКЦИЯ ЗДЕСЬ
            plan_to_archive = await dao.tariff_plan.get(session, id_=plan_id)
            if not plan_to_archive:
                return None  # Или HTTPException(404)

            if plan_to_archive.status != TariffStatusEnum.ARCHIVED:
                # dao.tariff_plan.update НЕ должен делать commit
                archived_plan = await dao.tariff_plan.update(
                    session,
                    db_obj=plan_to_archive,
                    obj_in=TariffPlanUpdate(
                        status=TariffStatusEnum.ARCHIVED, is_public=False
                    ),  # Передаем схему обновления
                )
                # await session.refresh(archived_plan) # Если update не делает refresh
                return archived_plan
            return plan_to_archive  # Уже был архивирован
