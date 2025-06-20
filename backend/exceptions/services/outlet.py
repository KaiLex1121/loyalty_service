from typing import Any, Dict, List, Optional

from backend.exceptions.common import (
    ConflictException,
    ForbiddenException,
    InternalServerError,
    NotFoundException,
    ValidationException,
)


class OutletNameConflictInCompanyException(ConflictException):
    def __init__(
        self,
        name: str,
        company_id: int,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not detail:
            detail = f"Outlet with name '{name}' already exists this company"
        _internal_details = {"name": name, "company_id": company_id}
        if internal_details:
            _internal_details.update(internal_details)
        super().__init__(detail=detail, internal_details=_internal_details)


class OutletNotFoundException(NotFoundException):
    def __init__(
        self,
        identifier: Any,
        identifier_type: str = "ID",
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not detail:
            detail = f"Outlet with {identifier_type} '{identifier}' not found."
        super().__init__(
            resource_name="Outlet",
            identifier=identifier,
            detail=detail,
            internal_details=internal_details,
        )


class OutletLimitExceededException(ConflictException):
    def __init__(
        self,
        company_id: int,
        limit: int,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not detail:
            detail = (
                f"Outlet limit exceeded for company ID '{company_id}'. Limit: {limit}."
            )
        _internal_details = {"company_id": company_id, "limit": limit}
        if internal_details:
            _internal_details.update(internal_details)
        super().__init__(detail=detail, internal_details=_internal_details)


class InvalidOutletForAssignmentException(ForbiddenException):
    def __init__(
        self,
        outlets_id: List[int],
        company_id: int,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ):
        if not detail:
            detail = f"Outlet IDs {outlets_id} do not belong to company ID {company_id} or are invalid for assignment."
        super().__init__(detail=detail, internal_details=internal_details)
