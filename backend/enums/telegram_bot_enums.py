import enum


class BotTypeEnum(enum.Enum):
    CUSTOMER = "customer"
    EMPLOYEE = "employee"


class BroadcastStatusEnum(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
