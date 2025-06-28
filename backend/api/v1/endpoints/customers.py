# backend/api/v1/endpoints/client_profile_router.py
from fastapi import APIRouter, Depends, Path, status  # Убрал HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import (
    get_customer_profile_service,
    get_customer_role_by_telegram_id_for_bot,
)
from backend.models.account import Account as AccountModel
from backend.models.customer_role import CustomerRole as CustomerRoleModel
from backend.schemas.customer_role import (  # Импортируем из нового файла
    CustomerBalanceResponse,
    CustomerRoleResponse,
)
from backend.services.company_customer import CustomerService

# from backend.core.logger import get_logger
# logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/{telegram_user_id}",
    response_model=CustomerRoleResponse,
    summary="Получить профиль клиента по Telegram ID",
    description="Возвращает информацию о профиле клиента по его Telegram ID.",
)
async def get_my_customer_profile_endpoint(
    customer_role_for_profile: CustomerRoleModel = Depends(
        get_customer_role_by_telegram_id_for_bot
    ),
    service: CustomerService = Depends(get_customer_profile_service),
):
    profile_data_model = await service.get_customer_profile(
        customer_role=customer_role_for_profile
    )
    return profile_data_model


@router.get(
    "/{telegram_user_id}/balance",
    response_model=CustomerBalanceResponse,
    summary="Получить текущий кэшбэк баланс клиента",
    description="Возвращает текущий кэшбэк баланс аутентифицированного клиента. "
    "Требует JWT токен клиента в заголовке Authorization.",
)
async def get_my_customer_balance_endpoint(
    customer_role_for_balance: CustomerRoleModel = Depends(
        get_customer_role_by_telegram_id_for_bot
    ),
    service: CustomerService = Depends(get_customer_profile_service),
):
    return await service.get_customer_balance(customer_role=customer_role_for_balance)
