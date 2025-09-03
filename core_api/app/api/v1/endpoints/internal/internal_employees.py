from typing import Union

# ... импорты ...
from app.core.dependencies import (
    get_current_employee_role,
    get_dao,
    get_employee_auth_service,
    get_employee_customer_interaction_service,
    get_session,
    verify_internal_api_key,
)
from app.dao.holder import HolderDAO
from app.exceptions.common import ForbiddenException, NotFoundException
from app.models.employee_role import EmployeeRole
from app.schemas.customer_bot_auth import CustomerProfileResponse
from app.schemas.employee_bot_auth import (
    EmployeeAuthChooseOutletResponse,
    EmployeeAuthResponse,
    EmployeeOtpRequest,
    EmployeeOtpVerify,
    EmployeeOutletSelectRequest,
)
from app.schemas.employee_customer_interaction import (
    AccrualRequestInternal,
    AccrueCashbackRequest,
)
from app.schemas.transaction import TransactionResponse
from app.services.employee_bot_auth import EmployeeAuthService
from app.services.employee_customer_interaction import (
    EmployeeCustomerInteractionService,
)
from app.services.otp_code import OtpCodeService
from app.services.otp_sending import MockOTPSendingService
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas.schemas import TokenPayload

router = APIRouter(dependencies=[Depends(verify_internal_api_key)])


@router.post("/auth/request-otp", summary="Request OTP for employee login")
async def request_employee_otp(
    request_data: EmployeeOtpRequest,
    company_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    service: EmployeeAuthService = Depends(get_employee_auth_service),
):
    otp = await service.request_otp_for_employee_login(
        session, request_data.work_phone_number, company_id
    )
    # ВАЖНО: В проде этот ответ должен быть пустым (204 No Content)
    return {"detail": "OTP has been sent.", "otp_for_testing": otp}


@router.post(
    "/auth/verify-otp",
    response_model=Union[EmployeeAuthResponse, EmployeeAuthChooseOutletResponse],
    summary="Verify OTP and get JWT or outlet list",
)
async def verify_employee_otp(
    verify_data: EmployeeOtpVerify,
    company_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    service: EmployeeAuthService = Depends(get_employee_auth_service),
):
    result = await service.verify_employee_otp(session, verify_data, company_id)
    return result


@router.post(
    "/auth/select-outlet",
    response_model=EmployeeAuthResponse,
    summary="Select outlet and get final JWT",
)
async def select_employee_outlet(
    select_data: EmployeeOutletSelectRequest,
    company_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    service: EmployeeAuthService = Depends(get_employee_auth_service),
):
    access_token = await service.select_outlet_and_create_token(
        session, select_data.phone_number, select_data.outlet_id, company_id
    )
    return access_token


@router.get(
    "/find-customer",
    response_model=CustomerProfileResponse,
    summary="Find a customer by phone number within the employee's company",
)
async def find_customer_by_phone(
    phone_number: str = Query(..., description="Phone number of the customer to find"),
    employee_data: tuple[EmployeeRole, TokenPayload] = Depends(
        get_current_employee_role
    ),  # <-- ЗАЩИТА
    session: AsyncSession = Depends(get_session),
    service: EmployeeCustomerInteractionService = Depends(
        get_employee_customer_interaction_service
    ),
):
    """
    Ищет профиль клиента по номеру телефона.
    Поиск ограничен компанией, в которой работает текущий сотрудник.
    """
    employee_role, token_payload = employee_data
    customer_role = await service.find_customer_by_phone_for_employee(
        session, phone_number, employee_role
    )

    return customer_role


@router.post(
    "/operations/accrue-cashback",
    response_model=TransactionResponse,
    summary="Accrue cashback for a customer",
)
async def accrue_cashback(
    accrual_data: AccrualRequestInternal,
    employee_data: tuple[EmployeeRole, TokenPayload] = Depends(
        get_current_employee_role
    ),
    session: AsyncSession = Depends(get_session),
    service: EmployeeCustomerInteractionService = Depends(
        get_employee_customer_interaction_service
    ),
):
    """
    Выполняет начисление кэшбэка клиенту от имени сотрудника.
    """
    current_employee, token_payload = employee_data

    # Извлекаем outlet_id из токена сотрудника
    outlet_id = token_payload.outlet_id
    if not outlet_id:
        raise ForbiddenException(
            "Operation cannot be performed: outlet ID is missing from token."
        )

    transaction = await service.accrue_cashback_for_customer(
        session=session,
        acting_employee_role=current_employee,
        customer_role_id=accrual_data.customer_role_id,
        purchase_amount=accrual_data.purchase_amount,
        outlet_id=outlet_id,
    )
    return transaction
