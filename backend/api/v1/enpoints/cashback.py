# backend/api/v1/endpoints/cashback_config.py
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import (
    get_cashback_service,
    get_dao,
    get_owned_company,
    get_session,
)
from backend.dao.holder import HolderDAO  # Для get_dao_holder
from backend.models.company import Company as CompanyModel
from backend.schemas.cashback import CashbackConfigResponse, CashbackConfigUpdate
from backend.services.cashback import CashbackService  # Ваш сервис

router = APIRouter()


@router.get(
    "/companies/{company_id}/cashback-config",
    response_model=CashbackConfigResponse,
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
    cashback_service: CashbackService = Depends(get_cashback_service),
):
    """
    Возвращает текущие настройки кэшбэка для указанной компании.
    Доступно владельцу компании или системному администратору.
    """
    return await cashback_service.get_cashback_config(
        session, company
    )  # Передаем session, хотя get_cashback_config может ее не использовать


@router.put(
    "/companies/{company_id}/cashback-config",
    response_model=CashbackConfigResponse,
    summary="Обновить конфигурацию кэшбэка для компании",
)
async def update_company_cashback_config_endpoint(
    update_data: CashbackConfigUpdate,
    company: CompanyModel = Depends(
        get_owned_company
    ),  # Зависимость проверяет права и загружает компанию с cashback_config
    session: AsyncSession = Depends(get_session),
    cashback_service: CashbackService = Depends(get_cashback_service),
):
    """
    Обновляет настройки кэшбэка для указанной компании.
    Доступно владельцу компании или системному администратору.
    """

    return await cashback_service.update_cashback_config(session, company, update_data)
