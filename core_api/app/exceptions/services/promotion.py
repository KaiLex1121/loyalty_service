# backend/exceptions/services/promotion.py
from typing import Any, Dict, List, Optional

from app.exceptions.base import BaseAppException
from app.exceptions.common import (
    ValidationException,  # Для ошибок валидации бизнес-логики
)
from app.exceptions.common import (  # Импортируем общие типы исключений
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from fastapi import status

# --- Promotion Service Specific Exceptions ---


class PromotionException(
    BaseAppException
):  # Базовое исключение для ошибок сервиса акций
    """Base exception for promotion service errors."""

    # Можно определить общий статус код, если применимо, или оставить как у BaseAppException
    # status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    # detail = "An error occurred in the promotion service."
    pass


class PromotionNotFoundException(NotFoundException):
    """Raised when a promotion is not found."""

    def __init__(
        self,
        identifier: Optional[Any] = None,
        company_id: Optional[int] = None,  # Дополнительный контекст
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ):
        if not detail:
            if identifier and company_id:
                detail = f"Promotion with identifier '{identifier}' not found for company ID {company_id}."
            elif identifier:
                detail = f"Promotion with identifier '{identifier}' not found."
            else:
                detail = "Promotion not found."
        super().__init__(
            resource_name="Promotion",
            identifier=identifier,
            detail=detail,
            internal_details=internal_details,
        )


class InvalidPromotionDataException(
    ValidationException
):  # Наследуемся от ValidationException (422)
    """Raised when promotion data is invalid for business logic (e.g., dates, type consistency)."""

    # detail по умолчанию будет "Validation error." от ValidationException
    # можно переопределить, если нужно более специфичное сообщение по умолчанию
    # detail = "Invalid promotion data provided."
    def __init__(
        self,
        detail: Optional[str] = None,
        field_errors: Optional[Dict[str, str]] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(detail=detail, internal_details=internal_details)
        self.field_errors = field_errors  # Можно использовать для передачи ошибок валидации конкретных полей в ответе


class PromotionCreationException(BadRequestException):
    """Raised when promotion creation fails."""

    detail = "Could not create promotion due to invalid data or conflict."

    def __init__(
        self,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail or self.detail, internal_details=internal_details
        )


class PromotionUpdateException(BadRequestException):
    """Raised when promotion update fails."""

    detail = "Could not update promotion due to invalid data or conflict."

    def __init__(
        self,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail or self.detail, internal_details=internal_details
        )


class PromotionDeletionException(BadRequestException):
    """Raised when promotion deletion fails (e.g., trying to delete an active promotion)."""

    detail = "Could not delete promotion."

    def __init__(
        self,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            detail=detail or self.detail, internal_details=internal_details
        )


class PromotionAlreadyExistsException(ConflictException):
    """Raised when a promotion with the same name already exists in a company."""

    def __init__(self, name: str, company_id: int):
        detail = (
            f"Promotion with name '{name}' already exists for company {company_id}."
        )
        super().__init__(detail=detail)
