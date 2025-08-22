# backend/exceptions/services/employee_auth.py
from typing import Any, Dict, Optional

from app.exceptions.base import BaseAppException
from app.exceptions.common import (  # Импортируем нужные
    BadRequestException,
    ForbiddenException,
    NotFoundException,
    ServiceUnavailableException,
    UnauthorizedException,
)
from fastapi import status


class EmployeeAuthException(BaseAppException):
    """Базовое исключение для ошибок аутентификации сотрудника."""

    detail = "Ошибка аутентификации сотрудника."


class EmployeeNotFoundInCompanyForLoginException(NotFoundException):
    def __init__(
        self,
        work_phone_number: str,
        company_id: int,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ):
        if not detail:
            detail = f"Сотрудник с рабочим номером телефона '{work_phone_number}' не найден в компании ID {company_id} или не имеет права на вход."
        super().__init__(
            resource_name="EmployeeRole",
            identifier=work_phone_number,
            detail=detail,
            internal_details=internal_details,
        )


class EmployeeAccountInactiveException(
    ForbiddenException
):  # Используем Forbidden (403)
    def __init__(
        self,
        account_id: int,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ):
        if not detail:
            detail = f"Аккаунт (ID: {account_id}), связанный с профилем сотрудника, неактивен."
        super().__init__(detail=detail, internal_details=internal_details)


class EmployeeOTPSendingException(
    ServiceUnavailableException
):  # Может быть 500 или 503
    detail = "Не удалось отправить OTP код сотруднику."

    def __init__(
        self,
        phone_number: str,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ):
        final_detail = detail or self.detail
        final_internal_details = internal_details or {}
        final_internal_details.setdefault("phone_number", phone_number)
        super().__init__(detail=final_detail, internal_details=final_internal_details)


class EmployeeOTPNotFoundException(NotFoundException):
    detail = (
        "Активный OTP код для сотрудника не найден. Пожалуйста, запросите новый код."
    )

    def __init__(
        self,
        account_id: int,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ):
        final_detail = detail or self.detail
        final_internal_details = internal_details or {}
        final_internal_details.setdefault("account_id", account_id)
        super().__init__(
            resource_name="OTP Code",
            detail=final_detail,
            internal_details=final_internal_details,
        )


class EmployeeOTPExpiredException(
    BadRequestException
):  # Код истек - это ошибка клиента (400)
    detail = "Срок действия OTP кода истек. Пожалуйста, запросите новый код."

    def __init__(
        self,
        otp_id: int,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ):
        final_detail = detail or self.detail
        final_internal_details = internal_details or {}
        final_internal_details.setdefault("otp_id", otp_id)
        super().__init__(detail=final_detail, internal_details=final_internal_details)


class InvalidEmployeeOTPException(
    BadRequestException
):  # Неверный код - ошибка клиента (400)
    detail = "Введен неверный OTP код."

    def __init__(
        self,
        otp_id: Optional[int] = None,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ):
        final_detail = detail or self.detail
        final_internal_details = internal_details or {}
        if otp_id:
            final_internal_details.setdefault("otp_id", otp_id)
        super().__init__(detail=final_detail, internal_details=final_internal_details)
