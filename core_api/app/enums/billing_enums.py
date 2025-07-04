import enum


class SubscriptionStatusEnum(str, enum.Enum):
    """Статус подписки компании на тарифный план."""

    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    EXPIRED = "expired"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    UNPAID = "unpaid"


class TariffStatusEnum(str, enum.Enum):
    """Статус тарифного плана."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    HIDDEN = "hidden"


class PaymentCycleEnum(str, enum.Enum):
    """Платежный цикл."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    HALF_YEARLY = "half_yearly"
    ANNUALLY = "annually"
    ONE_TIME = "one_time"  # Для разовых платежей


class CurrencyEnum(str, enum.Enum):
    """Валюта."""

    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class VatTypeEnum(
    str, enum.Enum
):  # Перенес сюда из general, т.к. больше относится к биллингу
    """Тип или ставка НДС."""

    NO_VAT = "no_vat"
    VAT_0 = "vat_0"
    VAT_10 = "vat_10"
    VAT_20 = "vat_20"
    VAT_INCLUDED = "vat_included"
