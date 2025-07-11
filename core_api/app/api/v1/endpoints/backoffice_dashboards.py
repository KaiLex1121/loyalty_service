from fastapi import APIRouter, Depends, HTTPException, Security

from app.core.dependencies import (
    get_current_active_account_with_profiles,
    get_dashboard_service,
)
from app.core.logger import get_logger
from app.core.security import oauth2_scheme_backoffice
from app.models.account import Account as AccountModel
from app.schemas.backoffice_dashboard import DashboardResponse
from app.services.backoffice_dashboard import DashboardService

router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
)
async def get_backoffice_dashboard(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
    current_account: AccountModel = Depends(get_current_active_account_with_profiles),
):
    """
    Возвращает информацию о текущем пользователе, его компаниях (владелец/сотрудник)
    и возможности создания новой компании.
    """
    dashboard_data = await dashboard_service.get_dashboard_data(
        current_account=current_account
    )
    return dashboard_data
