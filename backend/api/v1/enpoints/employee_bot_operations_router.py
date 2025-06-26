# backend/api/v1/endpoints/employee_bot_operations_router.py
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import (
    authenticate_employee_bot_and_get_company_id,  # Аутентификация самого бота (может быть не нужна, если эндпоинт защищен JWT сотрудника)
)
from backend.core.dependencies import (
    get_current_employee_role_for_bot_company,  # <--- Ключевая зависимость для аутентификации сотрудника
)
from backend.core.dependencies import (
    get_employee_customer_interaction_service,
    get_session,
)

# Схема OAuth2 для документации Swagger (если используется JWT сотрудника)
from backend.core.security import (  # Общая схема для получения токена, или специфичная для сотрудника
    oauth2_scheme_backoffice,
)
from backend.models.employee_role import (
    EmployeeRole as EmployeeRoleModel,  # Для аннотации типа
)
from backend.schemas.customer_role import (  # Используем эту схему для ответа
    CustomerRoleResponse,
)
from backend.schemas.employee_auth import CustomerSearchByPhoneRequest
from backend.services.employee_customer_interaction import (
    EmployeeCustomerInteractionService,
)

# Если мы создавали oauth2_scheme_employee_doc, то ее.
# Пока будем считать, что get_current_employee_role_for_bot_company
# сама использует нужный механизм получения токена.


# from backend.core.logger import get_logger
# logger = get_logger(__name__)

router = APIRouter()  # Префикс /employee-bot/operations будет задан при подключении


@router.post(
    "/customers/find-by-phone",
    response_model=CustomerRoleResponse,
    summary="Найти профиль клиента по номеру телефона (для сотрудника)",
    description="Аутентифицированный сотрудник (через JWT) ищет клиента своей компании по номеру телефона.",
    # dependencies=[Depends(oauth2_scheme)] # <--- Для Swagger, если JWT сотрудника используется
    # Если get_current_employee_role_for_bot_company использует oauth2_scheme, этого достаточно.
)
async def employee_find_customer_by_phone_endpoint(
    search_data: CustomerSearchByPhoneRequest,
    # Эта зависимость проверяет JWT сотрудника и его принадлежность к компании бота
    current_employee: EmployeeRoleModel = Depends(
        get_current_employee_role_for_bot_company
    ),
    service: EmployeeCustomerInteractionService = Depends(
        get_employee_customer_interaction_service
    ),
    session: AsyncSession = Depends(get_session),
):
    # Сервис найдет CustomerRole по номеру телефона клиента в компании сотрудника.
    # Ошибки (клиент не найден) будут обработаны глобально.
    customer_role = await service.find_customer_by_phone_for_employee(
        session,
        customer_phone_number=search_data.customer_phone_number,
        acting_employee_role=current_employee,
    )
    # FastAPI преобразует модель CustomerRole в CustomerProfileResponse
    return customer_role


# Здесь будут эндпоинты для начисления и списания кэшбэка сотрудником
# POST /customers/{customer_role_id}/accrue-cashback (принимает сумму покупки)
# POST /customers/{customer_role_id}/spend-cashback (принимает сумму списания)
# Они также будут защищены Depends(get_current_employee_role_for_bot_company)
# и будут принимать customer_role_id из пути (для которого сотрудник будет выполнять операцию).
