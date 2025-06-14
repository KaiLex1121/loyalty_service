from typing import Any, Dict, Optional

from backend.exceptions.common import (
    ConflictException,
    NotFoundException,
    ValidationException,
)


class AccountNotFoundException(NotFoundException):
    def __init__(
        self,
        identifier: Any,
        identifier_type: str = "ID",
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not detail:
            detail = f"Account with {identifier_type} '{identifier}' not found."
        super().__init__(
            resource_name="Account",
            identifier=identifier,
            detail=detail,
            internal_details=internal_details,
        )


class AccountCreationException(
    ValidationException
):  # Можно использовать BadRequestException или ValidationException
    detail = "Failed to create account."

    def __init__(
        self,
        reason: Optional[str] = None,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not detail and reason:
            detail = f"Failed to create account: {reason}"
        super().__init__(detail=detail, internal_details=internal_details)


class AccountUpdateException(ValidationException):
    detail = "Failed to update account."

    def __init__(
        self,
        account_id: Any,
        reason: Optional[str] = None,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not detail:
            detail = f"Failed to update account {account_id}"
            if reason:
                detail += f": {reason}"
        super().__init__(detail=detail, internal_details=internal_details)


class AccountAlreadyExistsException(ConflictException):
    def __init__(
        self,
        identifier: Any,
        identifier_type: str = "phone number",
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not detail:
            detail = f"Account with {identifier_type} '{identifier}' already exists."
        super().__init__(detail=detail, internal_details=internal_details)
