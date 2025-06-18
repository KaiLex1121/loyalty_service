# backend/api/v1/endpoints/outlets.py
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import (
    get_outlet_service,
    get_owned_company,
    get_session,
    get_verified_outlet_for_user,
)
from backend.models.company import Company as CompanyModel
from backend.models.outlet import Outlet as OutletModel
from backend.schemas.outlet import OutletCreate, OutletResponse, OutletUpdate
from backend.services.outlet import OutletService

router = APIRouter()


@router.post(
    "/companies/{company_id}/outlets",  # Путь для создания в контексте компании
    response_model=OutletResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую торговую точку для компании",
)
async def create_outlet_for_company_endpoint(
    company_id: int,  # Берется из пути - {company_id}
    outlet_data: OutletCreate,
    session: AsyncSession = Depends(get_session),
    company: CompanyModel = Depends(get_owned_company),
    outlet_service: OutletService = Depends(get_outlet_service),
):
    return await outlet_service.create_outlet(session, company, outlet_data)


@router.get(
    "/companies/{company_id}/outlets",
    response_model=List[OutletResponse],
    summary="Получить список торговых точек компании",
)
async def get_company_outlets_endpoint(
    company_id: int,  # Из пути
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    company: CompanyModel = Depends(get_owned_company),  # Проверка владения компанией
    outlet_service: OutletService = Depends(get_outlet_service),
):
    # company.id можно использовать для вызова сервиса
    return await outlet_service.get_outlets_for_company(
        session, company.id, skip, limit
    )


@router.get(
    "/outlets/{outlet_id}",  # Отдельный путь для конкретной ТТ
    response_model=OutletResponse,
    summary="Получить информацию о конкретной торговой точке",
)
async def get_outlet_by_id_endpoint(
    outlet: OutletModel = Depends(get_verified_outlet_for_user),
    get_outlet_service: OutletService = Depends(get_outlet_service),
):
    return await get_outlet_service.get_outlet(outlet)


@router.put(
    "/outlets/{outlet_id}",
    response_model=OutletResponse,
    summary="Обновить информацию о торговой точке",
)
async def update_outlet_endpoint(
    update_data: OutletUpdate,
    outlet_to_update: OutletModel = Depends(
        get_verified_outlet_for_user
    ),  # Зависимость получает объект и проверяет права
    session: AsyncSession = Depends(get_session),
    outlet_service: OutletService = Depends(get_outlet_service),
):
    return await outlet_service.update_outlet(session, outlet_to_update, update_data)


@router.delete(
    "/outlets/{outlet_id}",
    response_model=OutletResponse,  # Возвращаем обновленный (архивированный) объект
    summary="Архивировать (мягко удалить) торговую точку",
)
async def archive_outlet_endpoint(
    outlet_to_archive: OutletModel = Depends(
        get_verified_outlet_for_user
    ),  # Зависимость получает объект и проверяет права
    session: AsyncSession = Depends(get_session),
    outlet_service: OutletService = Depends(get_outlet_service),
):
    return await outlet_service.archive_outlet(session, outlet_to_archive)
