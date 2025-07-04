# backend/exceptions/services/client.py
from typing import Any, Dict, Optional

from app.exceptions.base import BaseAppException
from app.exceptions.common import (  # Импортируем нужные
    BadRequestException,
    ConflictException,
    NotFoundException,
)


class CustomerOnboardingException(
    BadRequestException
):  # Или BaseAppException, если нужен другой статус
    """Базовое исключение для ошибок онбординга клиента."""

    detail = "Ошибка при регистрации или входе клиента."


class TelegramIdConflictException(ConflictException):
    """Вызывается, когда предоставленный Telegram ID уже связан с другим аккаунтом."""

    def __init__(
        self,
        telegram_id: int,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ):
        if not detail:
            detail = (
                f"Telegram ID '{telegram_id}' уже используется другим пользователем."
            )
        super().__init__(detail=detail, internal_details=internal_details)


class PhoneNumberAlreadyLinkedToDifferentTelegramException(ConflictException):
    """Вызывается, когда номер телефона уже привязан к другому Telegram ID."""

    def __init__(
        self,
        phone_number: str,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ):
        if not detail:
            detail = f"Номер телефона '{phone_number}' уже используется другим Telegram аккаунтом."
        super().__init__(detail=detail, internal_details=internal_details)


class CompanyNotFoundForOnboardingException(NotFoundException):
    """Вызывается, когда компания для онбординга клиента не найдена или неактивна."""

    def __init__(
        self,
        company_id: int,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ):
        if not detail:
            detail = f"Компания с ID {company_id}, для которой производится регистрация клиента, не найдена или неактивна."
        super().__init__(
            resource_name="Company",
            identifier=company_id,
            detail=detail,
            internal_details=internal_details,
        )


class CustomerNotFoundByPhoneInCompanyException(NotFoundException):
    def __init__(
        self,
        phone_number: str,
        company_id: int,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ):
        if not detail:
            detail = f"Клиент с номером телефона '{phone_number}' не найден в компании ID {company_id}."
        super().__init__(
            resource_name="Клиент (поиск по телефону для сотрудника)",
            identifier=phone_number,
            detail=detail,
            internal_details=internal_details,
        )
