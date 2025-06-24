# backend/enums/loyalty_enums.py
import enum


class PromotionTypeEnum(
    str, enum.Enum
):  # Переименовал из PromotionType для единообразия
    """Основной тип механики акции."""

    CASHBACK = "cashback"  # Акция, изменяющая условия кэшбэка
    GIFT_AWARD = "gift_award"  # Акция, выдающая подарок
    POINTS_MULTIPLIER = "points_multiplier"  # Акция, умножающая баллы (если есть баллы)


class CashbackTypeEnum(str, enum.Enum):  # Переименовал из CashbackType
    """Тип модификатора кэшбэка в рамках акции."""

    PERCENTAGE = "percentage"  # Процент от суммы
    FIXED_AMOUNT = "fixed_amount"  # Фиксированная сумма


class GiftTypeEnum(str, enum.Enum):  # Переименовал из GiftType
    """Тип подарка или условия его получения в рамках акции."""

    NTH_ITEM_FREE = "nth_item_free"  # Каждый N-й товар бесплатно
    BUY_X_GET_Y_FREE = "buy_x_get_y_free"  # Купи X получи Y бесплатно (Y - конкретный товар или тот же)
    ACCUMULATION_GIFT = "accumulation_gift"  # Накопи X (покупок/суммы) получи подарок (можно объединить с THRESHOLD)
    PURCHASE_THRESHOLD_GIFT = "purchase_threshold_gift"  # Подарок за достижение суммы одной покупки или общей суммы покупок
    PRODUCT_GIFT = (
        "product_gift"  # Конкретный товар в подарок (может быть частью BUY_X_GET_Y)
    )


class PromotionStatusEnum(str, enum.Enum):  # Объединил и взял более полный вариант
    """Статус акции."""

    DRAFT = "draft"  # Черновик, не видна пользователям
    SCHEDULED = "scheduled"  # Запланирована к запуску
    ACTIVE = "active"  # Активна и действует
    PAUSED = "paused"  # Временно приостановлена
    FINISHED = "finished"  # Срок действия истек
    ARCHIVED = "archived"  # Перенесена в архив (заменил CANCELLED на ARCHIVED для согласованности)


class PromotionPriorityLevelEnum(str, enum.Enum):
    MINIMAL = "minimal"  # Минимальный
    LOW = "low"  # Низкий
    MEDIUM = "medium"  # Средний
    HIGH = "high"  # Высокий
    MAXIMUM = "maximum"  # Максимальный


class CustomerSegmentEnum(str, enum.Enum):  # Переименовал из CustomerSegment
    """Сегмент клиентов, на который нацелена акция или коммуникация."""

    ALL_CUSTOMERS = "all_customers"  # Все клиенты
    NEW_CUSTOMERS = (
        "new_customers"  # Новые клиенты (например, в течение X дней после регистрации)
    )
    VIP_CUSTOMERS = "vip_customers"  # VIP клиенты (по сумме покупок, частоте и т.д.)
    BIRTHDAY_CUSTOMERS = "birthday_customers"  # Именинники (в день рождения или в течение X дней до/после)
    REGULAR_CUSTOMERS = (
        "regular_customers"  # Постоянные клиенты (по RFM или другим критериям)
    )
    # Можно добавлять кастомные сегменты


class PromotionTriggerEnum(str, enum.Enum):  # Переименовал из PromotionTrigger
    """Условие (триггер) для активации/применения акции."""

    ON_PURCHASE = "on_purchase"  # При совершении покупки (основной)
    ON_REGISTRATION = "on_registration"  # При регистрации клиента
    ON_BIRTHDAY = "on_birthday"  # В день рождения клиента
    SCHEDULED_TIME = "scheduled_time"  # Активация по расписанию (для акций, не связанных с действием клиента)
    MANUAL_ACTIVATION = (
        "manual_activation"  # Ручная активация (например, персональная скидка)
    )


class TransactionTypeEnum(str, enum.Enum):
    """Тип финансовой транзакции в системе лояльности."""

    ACCRUAL_PURCHASE = "accrual_purchase"
    SPENDING_CASHBACK = "spending_cashback"
    ACCRUAL_MANUAL = "accrual_manual"  # Добавил для ручных операций
    SPENDING_MANUAL = "spending_manual"  # Добавил для ручных операций
    ACCRUAL_PROMOTION = "accrual_promotion"  # Если акция дает кэшбэк сверх базового
    ACCRUAL_REFUND = "accrual_refund"
    SPENDING_REFUND = "spending_refund"
    EXPIRATION = "expiration"


class TransactionStatusEnum(str, enum.Enum):  # Добавил этот Enum, который мы обсуждали
    """Статус транзакции."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERTED = "reverted"
    CANCELED = "canceled"
