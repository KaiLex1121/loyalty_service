from app.core.dependencies import (
    get_dao,
    get_employee_auth_service,
    get_session,
    verify_internal_api_key,
)
from app.dao.holder import HolderDAO
from app.schemas.employee_bot_auth import (
    EmployeeAuthResponse,
    EmployeeOtpRequest,
    EmployeeOtpVerify,
)
from app.services.employee_bot_auth import EmployeeAuthService
from app.services.otp_code import OtpCodeService
from app.services.otp_sending import MockOTPSendingService
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

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
    response_model=EmployeeAuthResponse,
    summary="Verify OTP and get JWT",
)
async def verify_employee_otp(
    verify_data: EmployeeOtpVerify,
    company_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    service: EmployeeAuthService = Depends(get_employee_auth_service),
):
    access_token = await service.verify_otp_and_create_token(
        session, verify_data, company_id
    )
    return access_token
