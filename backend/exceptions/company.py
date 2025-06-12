from backend.exceptions.base import NotFoundError, ServiceError, ValidationError


class CompanyServiceError(ServiceError):
    """Базовое исключение для CompanyService"""


class CompanyNotFoundError(NotFoundError):
    """Компания не найдена"""


class CompanyAlreadyExistsError(ValidationError):
    """Компания уже существует"""


class AccountNotFoundError(CompanyServiceError):
    """Аккаунт не найден или неактивен"""


class TrialPlanNotConfiguredError(CompanyServiceError):
    """Триальный план не настроен"""
