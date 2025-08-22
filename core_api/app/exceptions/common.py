from typing import Any, Dict, Optional

from app.exceptions.base import BaseAppException
from fastapi import status


class NotFoundException(BaseAppException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "The requested resource was not found."

    def __init__(
        self,
        resource_name: Optional[str] = None,
        identifier: Optional[Any] = None,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not detail:
            if resource_name and identifier:
                detail = f"{resource_name} with identifier '{identifier}' not found."
            elif resource_name:
                detail = f"{resource_name} not found."
        super().__init__(detail=detail, internal_details=internal_details)


class BadRequestException(BaseAppException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "The request is invalid."


class ValidationException(BadRequestException):  # Для ошибок валидации бизнес-логики
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "Validation error."


class UnauthorizedException(BaseAppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Authentication required."

    def __init__(
        self,
        detail: Optional[str] = None,
        internal_details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,  # Для WWW-Authenticate
    ) -> None:
        super().__init__(detail=detail, internal_details=internal_details)
        self.headers = headers


class ForbiddenException(BaseAppException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "You do not have permission to perform this action."


class ConflictException(BaseAppException):
    status_code = status.HTTP_409_CONFLICT
    detail = "A conflict occurred with the current state of the resource."


class InternalServerError(BaseAppException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "An unexpected internal server error occurred."


class ServiceUnavailableException(BaseAppException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    detail = "The service is temporarily unavailable."
