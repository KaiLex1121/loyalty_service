import enum


class CompanyStatusEnum(str, enum.Enum):
    """Статус компании в системе."""

    DRAFT = "draft"  # Черновик, не завершена регистрация
    PENDING_VERIFICATION = (
        "pending_verification"  # Ожидает проверки администрацией сервиса
    )
    ACTIVE = "active"  # Активна, полный доступ
    SUSPENDED = "suspended"  # Временно приостановлена
    LIMITED = "limited"  # Функционал ограничен
    REJECTED = "rejected"  # Заявка на активацию отклонена
    ARCHIVED = "archived"  # Перенесена в архив, неактивна


class OutletStatusEnum(str, enum.Enum):
    """Статус торговой точки."""

    OPEN = "open"  # Открыта и работает (заменил ACTIVE для ясности)
    TEMPORARILY_CLOSED = "temporarily_closed"  # Временно закрыта
    ARCHIVED = "archived"  # Перенесена в архив
    CLOSED_PERMANENTLY = "closed_permanently"  # Закрыта навсегда (архивирована)


class LegalFormEnum(str, enum.Enum):
    """Организационно-правовая форма компании."""

    OOO = "ООО"
    IP = "ИП"
    AO = "АО"  # Включая ПАО, НАО
    ZAO = "ЗАО"  # Устаревшая, но может встречаться
    SELF_EMPLOYED = "Самозанятый"
    OTHER = "Другое"
