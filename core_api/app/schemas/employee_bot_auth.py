# backend/schemas/employee_auth.py
from typing import Optional

from app.enums import OtpPurposeEnum  # Используем существующий или дополняем
from app.models.otp_code import OtpCode
from app.schemas.token import TokenResponse
from app.utils.validators import (  # Используем вашу схему ответа с токеном
    OTPCode,
    RussianPhoneNumber,
)
from pydantic import BaseModel, Field, constr

# Если OtpPurposeEnum нужно дополнить:
# class OtpPurposeEnum(str, enum.Enum):
#     REGISTRATION_OR_LOGIN_CLIENT = "registration_or_login_client"
#     BACKOFFICE_LOGIN = "backoffice_login"
#     EMPLOYEE_BOT_LOGIN = "employee_bot_login" # <--- НОВОЕ ЗНАЧЕНИЕ


# --- Схемы для OTP аутентификации сотрудника ---
class EmployeeOtpRequest(BaseModel):
    work_phone_number: RussianPhoneNumber


class EmployeeOtpVerify(BaseModel):
    work_phone_number: RussianPhoneNumber
    otp_code: OTPCode


class EmployeeAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
