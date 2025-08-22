# backend/api/v1/endpoints/outlets.py
from typing import List

from app.core.dependencies import (
    get_outlet_service,
    get_owned_company,
    get_session,
    get_verified_outlet_for_company,
)
from app.models.company import Company as CompanyModel
from app.models.outlet import Outlet as OutletModel
from app.schemas.company_outlet import OutletCreate, OutletResponse, OutletUpdate
from app.services.company_outlet import OutletService
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post(
    "/{company_id}/outlets",  # Путь для создания в контексте компании
    response_model=OutletResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую торговую точку для компании",
)
async def create_outlet_for_company_endpoint(
    outlet_data: OutletCreate,
    session: AsyncSession = Depends(get_session),
    company: CompanyModel = Depends(get_owned_company),
    outlet_service: OutletService = Depends(get_outlet_service),
):
    return await outlet_service.create_outlet(session, company, outlet_data)


@router.get(
    "/{company_id}/outlets",
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
    "/{company_id}/outlets/{outlet_id}",  # Отдельный путь для конкретной ТТ
    response_model=OutletResponse,
    summary="Получить информацию о конкретной торговой точке",
)
async def get_outlet_by_id_endpoint(
    company_id: int,
    outlet_id: int,
    outlet: OutletModel = Depends(get_verified_outlet_for_company),
    get_outlet_service: OutletService = Depends(get_outlet_service),
):
    return await get_outlet_service.get_outlet(outlet)


@router.put(
    "/{company_id}/outlets/{outlet_id}",
    response_model=OutletResponse,
    summary="Обновить информацию о торговой точке",
)
async def update_outlet_endpoint(
    update_data: OutletUpdate,
    outlet_to_update: OutletModel = Depends(
        get_verified_outlet_for_company
    ),  # Зависимость получает объект и проверяет права
    session: AsyncSession = Depends(get_session),
    outlet_service: OutletService = Depends(get_outlet_service),
):
    return await outlet_service.update_outlet(session, outlet_to_update, update_data)


@router.delete(
    "/{company_id}/outlets/{outlet_id}",
    response_model=OutletResponse,  # Возвращаем обновленный (архивированный) объект
    summary="Архивировать (мягко удалить) торговую точку",
)
async def archive_outlet_endpoint(
    company_id: int,
    outlet_id: int,
    outlet_to_archive: OutletModel = Depends(
        get_verified_outlet_for_company
    ),  # Зависимость получает объект и проверяет права
    session: AsyncSession = Depends(get_session),
    outlet_service: OutletService = Depends(get_outlet_service),
):
    return await outlet_service.archive_outlet(session, outlet_to_archive)
