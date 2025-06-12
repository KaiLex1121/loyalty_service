from backend.exceptions.base import BaseCustomException


class AuthServiceException(BaseCustomException):
    """Базовое исключение для сервиса аутентификации"""

    pass


class OTPSendingException(AuthServiceException):
    """Исключение для ошибок отправки OTP"""

    def __init__(self, phone_number: str):
        message = f"Failed to send OTP to phone number {phone_number}"
        super().__init__(
            message=message,
            status_code=503,
            detail="Could not send OTP SMS. Please try again later.",
        )


class OTPNotFoundException(AuthServiceException):
    """Исключение для случая, когда активный OTP не найден"""

    def __init__(self):
        message = "No active OTP found or OTP expired"
        super().__init__(
            message=message,
            status_code=400,
            detail="No active OTP found or OTP expired. Please request a new one.",
        )


class OTPExpiredException(AuthServiceException):
    """Исключение для истекшего OTP"""

    def __init__(self):
        message = "OTP has expired"
        super().__init__(
            message=message,
            status_code=400,
            detail="OTP has expired. Please request a new one.",
        )


class InvalidOTPException(AuthServiceException):
    """Исключение для невалидного OTP кода"""

    def __init__(self):
        message = "Invalid OTP code provided"
        super().__init__(message=message, status_code=400, detail="Invalid OTP code.")
