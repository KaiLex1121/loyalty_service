import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import (
    get_current_active_account_with_profiles, get_dao, get_dashboard_service,
    get_session)
from backend.dao.holder import HolderDAO
from backend.models.account import Account as AccountModel
from backend.schemas.account import AccountBase
from backend.schemas.dashboard import DashboardResponse
from backend.services.dashboard import DashboardService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
)
async def get_backoffice_dashboard(
    session: AsyncSession = Depends(get_session),
    dao: HolderDAO = Depends(get_dao),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
    current_account: AccountModel = Depends(
        get_current_active_account_with_profiles
    ),  # Получаем активный аккаунт с профилями
):
    """
    Возвращает информацию о текущем пользователе, его компаниях (владелец/сотрудник)
    и возможности создания новой компании.
    """
    try:
        dashboard_data = await dashboard_service.get_dashboard_data(
            current_account=current_account
        )
        return dashboard_data
    except Exception as e:
        logger.error(
            f"Error in get_backoffice_dashboard: {e}", exc_info=True
        )  # Замените на нормальный логгер
        raise HTTPException(
            status_code=500, detail="An error occurred while fetching dashboard data."
        )


@router.get("/", response_model=AccountBase)
async def read_users_me(
    current_account: AccountBase = Depends(get_current_active_account_with_profiles),
):
    return current_account
