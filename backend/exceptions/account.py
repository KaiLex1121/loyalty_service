from backend.exceptions.base import BaseCustomException


class AccountServiceException(BaseCustomException):
    """Базовое исключение для сервиса аккаунтов"""

    pass


class AccountNotFoundException(AccountServiceException):
    """Исключение для случая, когда аккаунт не найден"""

    def __init__(self, phone_number: str):
        message = f"Account with phone number {phone_number} not found"
        super().__init__(
            message=message,
            status_code=404,
            detail="Account with this phone number not found for OTP verification.",
        )


class AccountCreationException(AccountServiceException):
    """Исключение для ошибок при создании аккаунта"""

    def __init__(self, phone_number: str, reason: str = "Unknown error"):
        message = f"Failed to create account for phone number {phone_number}: {reason}"
        super().__init__(
            message=message,
            status_code=500,
            detail="Failed to create account. Please try again later.",
        )
