# backend/api/v1/endpoints/cashback_config.py
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    get_cashback_service,
    get_dao,
    get_owned_company,
    get_session,
)
from app.dao.holder import HolderDAO  # Для get_dao_holder
from app.models.company import Company as CompanyModel
from app.schemas.company_default_cashback_config import (
    CompanyDefaultCashbackConfigResponse,
    CompanyDefaultCashbackConfigUpdate,
)
from app.services.company_default_cashback_config import (  # Ваш сервис
    CompanyDefaultCashbackConfigService,
)

router = APIRouter()


@router.get(
    "/{company_id}/cashback-config",
    response_model=CompanyDefaultCashbackConfigResponse,
    summary="Получить конфигурацию кэшбэка для компании",
)
async def get_company_cashback_config_endpoint(
    # company_id: int = Path(..., title="ID компании"), # company_id уже есть в get_owned_company
    company: CompanyModel = Depends(
        get_owned_company
    ),  # Зависимость проверяет права и загружает компанию с cashback_config
    session: AsyncSession = Depends(
        get_session
    ),  # Нужна сервису (хотя в get_cashback_config он ее не использует для запросов)
    cashback_service: CompanyDefaultCashbackConfigService = Depends(
        get_cashback_service
    ),
):
    """
    Возвращает текущие настройки кэшбэка для указанной компании.
    Доступно владельцу компании или системному администратору.
    """
    return await cashback_service.get_cashback_config(
        session, company
    )  # Передаем session, хотя get_cashback_config может ее не использовать


@router.put(
    "/{company_id}/cashback-config",
    response_model=CompanyDefaultCashbackConfigResponse,
    summary="Обновить конфигурацию кэшбэка для компании",
)
async def update_company_cashback_config_endpoint(
    update_data: CompanyDefaultCashbackConfigUpdate,
    company: CompanyModel = Depends(
        get_owned_company
    ),  # Зависимость проверяет права и загружает компанию с cashback_config
    session: AsyncSession = Depends(get_session),
    cashback_service: CompanyDefaultCashbackConfigService = Depends(
        get_cashback_service
    ),
):
    """
    Обновляет настройки кэшбэка для указанной компании.
    Доступно владельцу компании или системному администратору.
    """

    return await cashback_service.update_cashback_config(session, company, update_data)
