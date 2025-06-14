from typing import Any, Dict, Optional

from backend.exceptions.common import (
    BadRequestException,
    NotFoundException,
    ServiceUnavailableException,
    ValidationException,
)


class InvalidOTPException(ValidationException):
    detail = "The provided OTP is invalid."

    def __init__(
        self,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(detail=detail, internal_details=internal_details)


class OTPExpiredException(ValidationException):
    detail = "The OTP has expired."

    def __init__(
        self,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(detail=detail, internal_details=internal_details)


class OTPNotFoundException(NotFoundException):
    detail = "Active OTP not found for the given criteria."

    def __init__(
        self,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            resource_name="OTP", detail=detail, internal_details=internal_details
        )


class OTPSendingException(
    ServiceUnavailableException
):  # Используем ServiceUnavailable, если это внешняя проблема
    detail = "Failed to send OTP."

    def __init__(
        self,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(detail=detail, internal_details=internal_details)
