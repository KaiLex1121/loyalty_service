# backend/enums/notification_enums.py
import enum


class NotificationStatusEnum(str, enum.Enum):
    """Статус уведомления/рассылки."""

    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"
    READ = "read"
    CANCELED = "canceled"
