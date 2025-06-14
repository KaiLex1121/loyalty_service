from typing import Any, Dict, Optional

from backend.exceptions.common import (
    InternalServerError,
    NotFoundException,
    ValidationException,
)


class CompanyFlowException(
    InternalServerError
):  # Для ошибок в логике флоу создания компании
    detail = "An error occurred during the company creation flow."

    def __init__(
        self,
        reason: str,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not detail:
            detail = f"Company creation flow failed: {reason}"
        super().__init__(detail=detail, internal_details=internal_details)


class TrialPlanNotConfiguredException(InternalServerError):
    detail = "Trial tariff plan is not configured in the system."

    def __init__(
        self,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(detail=detail, internal_details=internal_details)


class CompanyDataValidationException(ValidationException):
    detail = "Company data validation failed."

    def __init__(
        self,
        reason: str,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not detail:
            detail = f"Company data validation failed: {reason}"
        super().__init__(detail=detail, internal_details=internal_details)


class CompanyNotFoundException(NotFoundException):
    def __init__(
        self,
        identifier: Any,
        identifier_type: str = "ID",
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not detail:
            detail = f"Company with {identifier_type} '{identifier}' not found."
        super().__init__(
            resource_name="Company",
            identifier=identifier,
            detail=detail,
            internal_details=internal_details,
        )
