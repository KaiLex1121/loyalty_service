# backend/schemas/transaction.py
import datetime
import decimal
from typing import Optional

from app.enums import TransactionStatusEnum, TransactionTypeEnum
from app.schemas.promotion_usage import (  # Поместите импорт внутрь, если он циклический, или используйте ForwardRef
    PromotionUsageResponse,
)
from pydantic import BaseModel, Field


class TransactionBase(BaseModel):
    transaction_type: TransactionTypeEnum
    purchase_amount: Optional[decimal.Decimal] = Field(None, ge=0, examples=[1000.0])
    cashback_accrued: Optional[decimal.Decimal] = Field(None, ge=0, examples=[50.0])
    cashback_spent: Optional[decimal.Decimal] = Field(None, ge=0, examples=[20.0])
    description: Optional[str] = Field(
        None, examples=["Покупка товаров", "Списание кэшбэка"]
    )


class TransactionCreateInternal(
    TransactionBase
):  # Для внутреннего использования сервисами
    company_id: int
    customer_role_id: int
    outlet_id: Optional[int] = None
    status: TransactionStatusEnum = Field(default=TransactionStatusEnum.COMPLETED)
    balance_after: decimal.Decimal = Field(
        ..., description="Customer's cashback balance AFTER this transaction"
    )
    transaction_time: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    performed_by_employee_id: int
    # performed_by_admin_profile_id: Optional[int] = None # Для ручных операций админа


class TransactionUpdate(BaseModel):  # Обычно транзакции не обновляются
    status: Optional[TransactionStatusEnum] = (
        None  # Возможно, только статус (напр. отмена)
    )
    description: Optional[str] = None


class TransactionResponse(TransactionBase):
    id: int
    company_id: int
    customer_role_id: int
    outlet_id: Optional[int] = None
    status: TransactionStatusEnum
    balance_after: decimal.Decimal
    transaction_time: datetime.datetime

    created_at: datetime.datetime
    updated_at: datetime.datetime

    promotion_usage: Optional[PromotionUsageResponse] = None

    class Config:
        from_attributes = True


# Для решения циклического импорта, если PromotionUsageResponse импортирует TransactionResponse
# TransactionResponse.model_rebuild() # Pydantic v2
# PromotionUsageResponse.update_forward_refs() # Pydantic v1, если использовали ForwardRef


class TransactionListResponseItem(BaseModel):  # Для списков транзакций
    id: int
    transaction_type: TransactionTypeEnum
    status: TransactionStatusEnum
    transaction_time: datetime.datetime
    purchase_amount: Optional[decimal.Decimal]
    cashback_accrued: Optional[decimal.Decimal]
    cashback_spent: Optional[decimal.Decimal]
    balance_after: decimal.Decimal
    # promotion_name: Optional[str] = None # Можно добавить денормализованное имя акции

    class Config:
        from_attributes = True
