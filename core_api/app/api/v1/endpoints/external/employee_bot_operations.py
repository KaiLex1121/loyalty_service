# backend/api/v1/endpoints/employee_bot_operations_router.py
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    authenticate_employee_bot_and_get_company_id,  # Аутентификация самого бота (может быть не нужна, если эндпоинт защищен JWT сотрудника)
)
from app.core.dependencies import (
    get_current_employee_role_for_bot_company,  # <--- Ключевая зависимость для аутентификации сотрудника
)
from app.core.dependencies import (
    get_employee_customer_interaction_service,
    get_session,
)

# Схема OAuth2 для документации Swagger (если используется JWT сотрудника)
from app.core.security import (  # Общая схема для получения токена, или специфичная для сотрудника
    oauth2_scheme_backoffice,
)
from app.models.customer_role import CustomerRole
from app.models.employee_role import (
    EmployeeRole as EmployeeRoleModel,  # Для аннотации типа
)
from app.schemas.customer_bot_auth import CustomerProfileResponse
from app.schemas.customer_role import (  # Используем эту схему для ответа
    CustomerRoleResponse,
)
from app.schemas.employee_customer_interaction import (
    AccrueCashbackRequest,
    CustomerSearchByPhoneRequest,
    SpendCashbackRequestOTP,
    SpendCashbackRequestOTPResponse,
    SpendCashbackVerifyOTP,
)
from app.schemas.transaction import TransactionResponse
from app.services.employee_customer_interaction import (
    EmployeeCustomerInteractionService,
)

router = APIRouter()


@router.post(
    "/customers/find-by-phone",
    response_model=CustomerProfileResponse,
    summary="Найти профиль клиента по номеру телефона (для сотрудника)",
)
async def employee_find_customer_by_phone_endpoint(
    search_data: CustomerSearchByPhoneRequest,
    current_employee: EmployeeRoleModel = Depends(
        get_current_employee_role_for_bot_company
    ),
    service: EmployeeCustomerInteractionService = Depends(
        get_employee_customer_interaction_service
    ),
    session: AsyncSession = Depends(get_session),
):
    customer_role = await service.find_customer_by_phone_for_employee(
        session,
        customer_phone_number=search_data.customer_phone_number,
        acting_employee_role=current_employee,
    )
    return customer_role


@router.post(
    "/customers/accrue-cashback",  # <--- ПУТЬ ИЗМЕНЕН
    response_model=TransactionResponse,
    summary="Начислить кэшбэк клиенту (для сотрудника)",
)
async def employee_accrue_cashback_for_customer_endpoint(
    accrue_data: AccrueCashbackRequest,  # <--- Схема теперь содержит customer_phone_number
    current_employee: EmployeeRoleModel = Depends(
        get_current_employee_role_for_bot_company
    ),
    service: EmployeeCustomerInteractionService = Depends(
        get_employee_customer_interaction_service
    ),
    session: AsyncSession = Depends(get_session),
):
    transaction = await service.accrue_cashback_for_customer(
        session=session,
        acting_employee_role=current_employee,
        customer_phone_number=accrue_data.customer_phone_number,
        purchase_amount=accrue_data.purchase_amount,
        outlet_id=accrue_data.outlet_id,
    )
    return transaction


@router.post(
    "/customers/spend-cashback/request-otp",  # <--- ПУТЬ ИЗМЕНЕН
    response_model=SpendCashbackRequestOTPResponse,
    summary="Шаг 1: Запросить OTP для списания кэшбэка",
)
async def employee_request_spend_otp_endpoint(
    request_data: SpendCashbackRequestOTP,  # <--- Схема теперь содержит customer_phone_number
    current_employee: EmployeeRoleModel = Depends(
        get_current_employee_role_for_bot_company
    ),
    service: EmployeeCustomerInteractionService = Depends(
        get_employee_customer_interaction_service
    ),
    session: AsyncSession = Depends(get_session),
):
    amount_to_spend, masked_phone = await service.request_spend_otp(
        session=session,
        acting_employee_role=current_employee,
        customer_phone_number=request_data.customer_phone_number,
        purchase_amount=request_data.purchase_amount,
    )
    return SpendCashbackRequestOTPResponse(
        amount_to_spend=amount_to_spend, customer_phone_masked=masked_phone
    )


@router.post(
    "/customers/spend-cashback/confirm",  # <--- ПУТЬ ИЗМЕНЕН
    response_model=TransactionResponse,
    summary="Шаг 2: Подтвердить списание кэшбэка с помощью OTP",
)
async def employee_confirm_spend_otp_endpoint(
    verify_data: SpendCashbackVerifyOTP,  # <--- Схема теперь содержит customer_phone_number
    current_employee: EmployeeRoleModel = Depends(
        get_current_employee_role_for_bot_company
    ),
    service: EmployeeCustomerInteractionService = Depends(
        get_employee_customer_interaction_service
    ),
    session: AsyncSession = Depends(get_session),
):
    transaction = await service.confirm_spend_with_otp(
        session=session,
        acting_employee_role=current_employee,
        customer_phone_number=verify_data.customer_phone_number,
        otp_code=verify_data.otp_code,
        purchase_amount=verify_data.purchase_amount,
        outlet_id=verify_data.outlet_id,
    )
    return transaction
