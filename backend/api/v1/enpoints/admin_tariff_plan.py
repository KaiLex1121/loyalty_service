from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_session  # Ваша зависимость для сессии
from backend.core.dependencies import get_current_full_system_admin, get_dao
from backend.dao.holder import HolderDAO
from backend.schemas.tariff_plan import (
    TariffPlanCreate,
    TariffPlanResponse,
    TariffPlanUpdate,
)
from backend.services.admin_tariff_plan import AdminTariffPlanService

router = APIRouter()


@router.post(
    "",
    response_model=TariffPlanResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_full_system_admin)],
)
async def create_new_tariff_plan_endpoint(
    tariff_plan_data: TariffPlanCreate,
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
    admin_tariff_plan_service: AdminTariffPlanService = Depends(),
):
    new_plan = await admin_tariff_plan_service.create_tariff_plan(
        session, dao, tariff_plan_data
    )
    return new_plan


@router.get(
    "/{plan_id}",
    response_model=TariffPlanResponse,
    dependencies=[Depends(get_current_full_system_admin)],
)
async def read_tariff_plan_endpoint(
    plan_id: int,
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
    admin_tariff_plan_service: AdminTariffPlanService = Depends(),
):
    plan = await admin_tariff_plan_service.get_tariff_plan(session, dao, plan_id)
    return plan


@router.get(
    "",
    response_model=List[TariffPlanResponse],
    dependencies=[Depends(get_current_full_system_admin)],
)
async def read_all_tariff_plans_endpoint(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
    admin_tariff_plan_service: AdminTariffPlanService = Depends(),
):
    plans = await admin_tariff_plan_service.get_all_tariff_plans(
        session, dao, skip=skip, limit=limit
    )
    return [plan for plan in plans]


@router.put(
    "/{plan_id}",
    response_model=TariffPlanResponse,
    dependencies=[Depends(get_current_full_system_admin)],
)
async def update_existing_tariff_plan_endpoint(
    plan_id: int,
    plan_update_data: TariffPlanUpdate,
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
    admin_tariff_plan_service: AdminTariffPlanService = Depends(),
):

    updated_plan = await admin_tariff_plan_service.update_tariff_plan(
        session, dao, plan_id, plan_update_data
    )
    return updated_plan


@router.delete(
    "/{plan_id}",
    response_model=TariffPlanResponse,
    summary="Archive a tariff plan",
    dependencies=[Depends(get_current_full_system_admin)],
)
async def archive_tariff_plan_endpoint(
    plan_id: int,
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
    admin_tariff_plan_service: AdminTariffPlanService = Depends(),
):

    archived_plan = await admin_tariff_plan_service.archive_tariff_plan(
        session, dao, plan_id
    )
    return archived_plan
