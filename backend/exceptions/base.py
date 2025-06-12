class ServiceError(Exception):
    """Базовое исключение для всех сервисов"""


class ValidationError(ServiceError):
    """Ошибки валидации данных"""


class NotFoundError(ServiceError):
    """Ресурс не найден"""


class PermissionDeniedError(ServiceError):
    """Недостаточно прав"""


class AccountNotFoundError(ServiceError):
    """Аккаунт не найден"""
