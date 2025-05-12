import enum


class UserRole(enum.Enum):
    ADMIN = "admin"
    BUSINESS_OWNER = "business_owner"
    STAFF = "staff"
    CLIENT = "client"


class TransactionType(enum.Enum):
    CASHBACK_ACCRUAL = "cashback_accrual"
    CASHBACK_WITHDRAWAL = "cashback_withdrawal"


class BroadcastStatus(enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENT = "sent"
    FAILED = "failed"


class FeedbackStatus(enum.Enum):
    NEW = "new"
    READ = "read"
    ANSWERED = "answered"
