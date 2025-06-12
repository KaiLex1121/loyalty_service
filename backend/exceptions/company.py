from backend.exceptions.base import NotFoundError, ServiceError, ValidationError


class CompanyServiceError(ServiceError):
    """Базовое исключение для CompanyService"""

    pass


class CompanyNotFoundError(NotFoundError):
    """Компания не найдена"""

    pass


class CompanyAlreadyExistsError(ValidationError):
    """Компания уже существует"""

    pass


class AccountNotFoundError(CompanyServiceError):
    """Аккаунт не найден или неактивен"""

    pass


class TrialPlanNotConfiguredError(CompanyServiceError):
    """Триальный план не настроен"""

    pass
