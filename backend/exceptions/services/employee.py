from typing import Any, Dict, Optional

from backend.exceptions.common import (
    ConflictException,
    ForbiddenException,
    InternalServerError,
    NotFoundException,
    ValidationException,
)


class EmployeeAlreadyExistsInCompanyException(ConflictException):

    def __init__(
        self,
        employee_phone_number: str,
        company_id: int,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not detail:
            detail = f"Employee with phone number '{employee_phone_number}' already exists in company with ID {company_id}."
        _internal_details = {
            "phone number": employee_phone_number,
            "company_id": company_id,
        }
        if internal_details:
            _internal_details.update(internal_details)
        super().__init__(detail=detail, internal_details=_internal_details)


class EmployeeLimitExceededException(ConflictException):
    def __init__(
        self,
        company_id: int,
        limit: int,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not detail:
            detail = f"Employee limit exceeded for company ID '{company_id}'. Limit: {limit}."
        _internal_details = {"company_id": company_id, "limit": limit}
        if internal_details:
            _internal_details.update(internal_details)
        super().__init__(detail=detail, internal_details=_internal_details)


class EmployeeNotFoundException(NotFoundException):
    def __init__(
        self,
        identifier: Any,
        identifier_type: str = "ID",
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not detail:
            detail = f"Employee with {identifier_type} '{identifier}' not found."
        super().__init__(
            resource_name="Employee",
            identifier=identifier,
            detail=detail,
            internal_details=internal_details,
        )
