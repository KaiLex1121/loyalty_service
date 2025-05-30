from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from backend.core.dependencies import get_session # Ваша зависимость для сессии
from backend.core.dependencies import get_dao
from backend.core.dependencies import get_current_full_system_admin
from backend.dao.holder import HolderDAO
from backend.schemas.tariff_plan import TariffPlanCreate, TariffPlanUpdate, TariffPlanResponse
from backend.services.admin_tariff_plan import admin_tariff_plan_service
# from backend.models.admin_profile import AdminProfile as AdminProfileModel # Не нужен здесь, если get_current_full_system_admin возвращает AdminProfile

router = APIRouter()


@router.post(
    "",
    response_model=TariffPlanResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_full_system_admin)]
)
async def create_new_tariff_plan_endpoint( # Переименовал для ясности
    plan_data: TariffPlanCreate,
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao) # Инжектим HolderDAO
):
    try:
        # Сервис сам управляет транзакцией session.begin()
        new_plan = await admin_tariff_plan_service.create_tariff_plan(session, dao, plan_data)
        return TariffPlanResponse.model_validate(new_plan)
    except HTTPException:
        raise
    except Exception as e: # Ловим общие ошибки, если сервис их не обработал в HTTPException
        # logger.error(f"Error creating tariff plan: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{plan_id}", response_model=TariffPlanResponse, dependencies=[Depends(get_current_full_system_admin)])
async def read_tariff_plan_endpoint( # Переименовал
    plan_id: int,
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao)
):
    plan = await admin_tariff_plan_service.get_tariff_plan(session, dao, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tariff plan not found")
    return TariffPlanResponse.model_validate(plan)


@router.get("", response_model=List[TariffPlanResponse], dependencies=[Depends(get_current_full_system_admin)])
async def read_all_tariff_plans_endpoint( # Переименовал
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao)
):
    plans = await admin_tariff_plan_service.get_all_tariff_plans(session, dao, skip=skip, limit=limit)
    return [TariffPlanResponse.model_validate(plan) for plan in plans]


@router.put("/{plan_id}", response_model=TariffPlanResponse, dependencies=[Depends(get_current_full_system_admin)])
async def update_existing_tariff_plan_endpoint( # Переименовал
    plan_id: int,
    plan_update_data: TariffPlanUpdate,
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao)
):
    try:
        updated_plan = await admin_tariff_plan_service.update_tariff_plan(session, dao, plan_id, plan_update_data)
        if not updated_plan: # Сервис может вернуть None, если план не найден
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tariff plan not found to update")
        return TariffPlanResponse.model_validate(updated_plan)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{plan_id}", response_model=TariffPlanResponse, summary="Archive a tariff plan", dependencies=[Depends(get_current_full_system_admin)])
async def archive_tariff_plan_endpoint( # Переименовал
    plan_id: int,
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao)
):
    try:
        archived_plan = await admin_tariff_plan_service.archive_tariff_plan(session, dao, plan_id)
        if not archived_plan: # Сервис может вернуть None
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tariff plan not found to archive")
        return TariffPlanResponse.model_validate(archived_plan)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
