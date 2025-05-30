import enum


class SubscriptionStatusEnum(str, enum.Enum):
    """Статус подписки компании на тарифный план."""

    TRIALING = "trialing"  # На пробном периоде
    ACTIVE = "active"  # Активна, оплачена
    PAST_DUE = "past_due"  # Просрочен платеж
    CANCELED = "canceled"  # Отменена (пользователем или системой до окончания периода)
    EXPIRED = "expired"  # Истек срок действия (если не было автопродления)
    INCOMPLETE = "incomplete"  # Создание подписки не завершено (например, не прошел первый платеж)
    INCOMPLETE_EXPIRED = (
        "incomplete_expired"  # Время на завершение создания подписки истекло
    )
    UNPAID = "unpaid"  # Не оплачена (после past_due, если не отменена)


class CompanyStatusEnum(str, enum.Enum):
    """Статус компании."""

    DRAFT = "draft"  # Черновик
    ACTIVE = "active"  # Активна и работает
    PENDING_VERIFICATION = "pending_verification"  # Ожидает проверки данных
    SUSPENDED = "suspended"  # Временно приостановлена (например, за неуплату)
    ARCHIVED = "archived"  # Перенесена в архив, неактивна


class OutletStatusEnum(str, enum.Enum):
    """Статус торговой точки."""

    ACTIVE = "active"  # Активна и работает
    ARCHIVED = "archived"  # Закрыта навсегда (архивирована)


class PromotionStatusEnum(str, enum.Enum):
    """Статус акции."""

    DRAFT = "draft"  # Черновик, не видна пользователям
    SCHEDULED = "scheduled"  # Запланирована к запуску
    ACTIVE = "active"  # Активна и действует
    PAUSED = "paused"  # Временно приостановлена
    EXPIRED = "expired"  # Срок действия истек
    ARCHIVED = "archived"  # Перенесена в архив


class OtpPurposeEnum(str, enum.Enum):
    """
    Назначение OTP кода.
    """

    BACKOFFICE_LOGIN = "backoffice_login"  # Для входа в систему
    PHONE_RESET = "phone_reset"  # Для сброса номера телефона
    TRANSACTION_CONFIRM = (
        "transaction_confirm"  # Для подтверждения важных транзакций/операций
    )
    EMAIL_VERIFICATION = "email_verification"  # Для верификации email


class NotificationStatusEnum(str, enum.Enum):
    """
    Статус уведомления/рассылки.
    """

    PENDING = "pending"  # В ожидании отправки (например, в очереди)
    PROCESSING = "processing"  # В процессе отправки
    SENT = "sent"  # Отправлено шлюзу/сервису рассылок
    FAILED = "failed"  # Не удалось отправить
    DELIVERED = (
        "delivered"  # Доставлено получателю (если есть такая информация от провайдера)
    )
    READ = "read"  # Прочитано получателем (если есть такая информация)
    CANCELED = "canceled"  # Отменено до отправки


class TransactionTypeEnum(str, enum.Enum):
    """
    Тип финансовой транзакции в системе лояльности.
    """

    ACCRUAL_PURCHASE = "accrual_purchase"  # Начисление за покупку
    SPENDING_CASHBACK = "spending_cashback"  # Списание кэшбэка на оплату
    ACCRUAL_REFUND = "accrual_refund"  # Возврат списанного кэшбэка (например, при отмене покупки, где был списан кэшбэк)
    SPENDING_REFUND = "spending_refund"  # Списание начисленного кэшбэка (например, при возврате товара, за который был начислен кэшбэк)
    EXPIRATION = (
        "expiration"  # Сгорание кэшбэка по сроку действия (если будет такая логика)
    )


class PromotionTypeEnum(str, enum.Enum):
    """
    Тип акции.
    """

    PERCENTAGE_CASHBACK = "percentage_cashback"  # Повышенный/пониженный процент кэшбэка
    FIXED_AMOUNT_CASHBACK = (
        "fixed_amount_cashback"  # Фиксированная сумма кэшбэка за действие/покупку
    )
    BONUS_POINTS = (
        "bonus_points"  # Начисление бонусных баллов (если баллы отличаются от кэшбэка)
    )
    PRODUCT_DISCOUNT = "product_discount"  # Скидка на товар/услугу (может быть вне логики кэшбэка, но для полноты)
    GIFT = "gift"  # Подарок за покупку/действие


class UserAccessLevelEnum(str, enum.Enum):
    """
    Уровень доступа пользователя.
    """

    FULL_ADMIN = "full_admin"
    COMPANY_OWNER = "company_owner"
    COMPANY_MANAGER = "company_manager"
    SUPPORT_SPECIALIST = "support_specialist"


class LegalFormEnum(str, enum.Enum):
    OOO = "ООО"
    IP = "ИП"
    AO = "АО"
    ZAO = "ЗАО"
    SELF_EMPLOYED = "Самозанятый"
    OTHER = "Другое"


class TariffStatusEnum(str, enum.Enum):
    ACTIVE = "active"  # Доступен для выбора
    ARCHIVED = "archived"  # Больше не доступен для новых подписок, но старые могут продолжать работать
    HIDDEN = "hidden"  # Не отображается публично, но может быть назначен вручную


class PaymentCycleEnum(str, enum.Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    HALF_YEARLY = "half_yearly"
    ANNUALLY = "annually"


class CurrencyEnum(str, enum.Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
