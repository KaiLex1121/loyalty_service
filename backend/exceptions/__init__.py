from backend.exceptions.base import BaseAppException
from backend.exceptions.common import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    InternalServerError,
    NotFoundException,
    ServiceUnavailableException,
    UnauthorizedException,
    ValidationException,
)
from backend.exceptions.services.account import (
    AccountAlreadyExistsException,
    AccountCreationException,
    AccountNotFoundException,
    AccountUpdateException,
)
from backend.exceptions.services.backoffice_auth import (
    InvalidOTPException,
    OTPExpiredException,
    OTPNotFoundException,
    OTPSendingException,
)
from backend.exceptions.services.company import (
    BasePlanNotConfiguredException,
    CompanyDataValidationException,
    CompanyFlowException,
    CompanyNotFoundException,
)
from backend.exceptions.services.subscription import SubscriptionNotFoundException

__all__ = [
    "BaseAppException",
    "SubscriptionNotFoundException",
    "BadRequestException",
    "ConflictException",
    "ForbiddenException",
    "InternalServerError",
    "NotFoundException",
    "ServiceUnavailableException",
    "UnauthorizedException",
    "ValidationException",
    "AccountCreationException",
    "AccountNotFoundException",
    "AccountUpdateException",
    "AccountAlreadyExistsException",
    "InvalidOTPException",
    "OTPExpiredException",
    "OTPNotFoundException",
    "OTPSendingException",
    "CompanyFlowException",
    "CompanyDataValidationException",
    "CompanyNotFoundException",
    "SubscriptionNotFoundException",
    "BasePlanNotConfiguredException",
]
