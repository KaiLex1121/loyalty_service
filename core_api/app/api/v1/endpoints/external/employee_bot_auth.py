# backend/api/v1/endpoints/employee_bot_auth_router.py
from app.core.dependencies import (
    authenticate_employee_bot_and_get_company_id,  # Аутентификация самого бота
)
from app.core.dependencies import (
    get_employee_auth_service,  # Сервис для OTP логики сотрудника
)
from app.core.dependencies import (
    get_session,
)

# EmployeeRoleResponse может понадобиться, если request_otp возвращает данные сотрудника
from app.schemas.company_employee import (  # Простая схема для ответа после запроса OTP
    EmployeeSummaryForOtpResponse,
)
from app.schemas.employee_bot_auth import (
    EmployeeOtpVerify,  # Верификация OTP сотрудником
)
from app.schemas.employee_bot_auth import (  # Запрос OTP сотрудником
    EmployeeOtpRequest,
)
from app.schemas.token import TokenResponse  # Ответ с JWT токеном
from app.services.employee_bot_auth import EmployeeAuthService
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# from backend.core.logger import get_logger
# logger = get_logger(__name__)

router = APIRouter()  # Префикс /employee-bot/auth будет задан при подключении


@router.post(
    "/request-otp/{bot_token}",
    response_model=EmployeeSummaryForOtpResponse,
    status_code=status.HTTP_200_OK,
    summary="Запросить OTP для входа сотрудника в бот",
    description="Сотрудник вводит свой рабочий номер телефона. Бот (аутентифицированный по API-ключу) "
    "передает этот номер для генерации и отправки OTP.",
)
async def employee_request_otp_endpoint(
    otp_request_data: EmployeeOtpRequest,
    bot_company_id: int = Depends(authenticate_employee_bot_and_get_company_id),
    service: EmployeeAuthService = Depends(get_employee_auth_service),
    session: AsyncSession = Depends(get_session),
):
    # Сервис найдет EmployeeRole по work_phone_number и bot_company_id,
    # сгенерирует OTP и отправит его.
    # Глобальные хендлеры обработают ошибки из сервиса.
    employee_role = await service.request_otp_for_employee_login(
        session,
        work_phone_number=otp_request_data.work_phone_number,
        bot_company_id=bot_company_id,
    )
    # Возвращаем какую-то информацию, подтверждающую, для кого запрошен OTP,
    # или просто статус 200 OK, если не хотим раскрывать детали до входа.
    # EmployeeSummaryForOtpResponse - это Pydantic схема, которую нужно будет создать.
    return EmployeeSummaryForOtpResponse(
        employee_role_id=employee_role.id,
        work_phone_number=employee_role.work_phone_number,
        message="OTP успешно отправлен.",  # Опционально
    )


@router.post(
    "/verify-otp/{bot_token}",
    response_model=TokenResponse,  # В случае успеха возвращаем JWT токен
    summary="Верифицировать OTP и аутентифицировать сотрудника в боте",
    description="Сотрудник вводит полученный OTP. Бот (аутентифицированный по API-ключу) "
    "передает данные для верификации. В случае успеха выдается JWT токен для сотрудника.",
)
async def employee_verify_otp_and_login_endpoint(
    otp_verify_data: EmployeeOtpVerify,  # Содержит work_phone_number и otp_code
    bot_company_id: int = Depends(authenticate_employee_bot_and_get_company_id),
    service: EmployeeAuthService = Depends(get_employee_auth_service),
    session: AsyncSession = Depends(get_session),
):
    # Сервис проверит OTP и, если все хорошо, сгенерирует и вернет TokenResponse.
    # Ошибки (неверный OTP, истекший OTP, сотрудник не найден) будут обработаны глобально.
    token_response = await service.verify_otp_and_login_employee(
        session, otp_data=otp_verify_data, bot_company_id=bot_company_id
    )
    return token_response
