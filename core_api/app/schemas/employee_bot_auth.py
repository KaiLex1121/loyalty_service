# backend/schemas/employee_auth.py
from typing import Optional

from app.enums import OtpPurposeEnum  # Используем существующий или дополняем
from app.models.otp_code import OtpCode
from app.schemas.company_outlet import OutletResponseForEmployee
from app.schemas.token import TokenResponse
from pydantic import BaseModel, Field, constr

from shared.utils.validators import (  # Используем вашу схему ответа с токеном
    OTPCode,
    RussianPhoneNumber,
)


# --- Схемы для OTP аутентификации сотрудника ---
class EmployeeOtpRequest(BaseModel):
    work_phone_number: RussianPhoneNumber


class EmployeeOtpVerify(BaseModel):
    work_phone_number: RussianPhoneNumber
    otp_code: OTPCode


class EmployeeOutletSelectRequest(BaseModel):
    phone_number: str  # Для идентификации сессии
    outlet_id: int


class EmployeeAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EmployeeAuthChooseOutletResponse(BaseModel):
    outlets: list[OutletResponseForEmployee]
