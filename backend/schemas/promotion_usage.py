# backend/schemas/promotion_usage.py
import datetime
import decimal
from typing import Optional

from pydantic import BaseModel, Field


class PromotionUsageBase(BaseModel):
    cashback_accrued: decimal.Decimal = Field(..., ge=0, examples=[50.0])


class PromotionUsageCreate(PromotionUsageBase):
    # Эта схема может не использоваться напрямую в API,
    # так как PromotionUsage создается сервисом CashbackCalculationService.
    pass


class PromotionUsageUpdate(BaseModel):
    pass


class PromotionUsageCreateInternal(PromotionUsageBase):
    promotion_id: int
    customer_role_id: int
    transaction_id: int  # Связь с транзакцией обязательна


class PromotionUsageResponse(PromotionUsageBase):
    id: int
    promotion_id: int
    customer_role_id: int
    transaction_id: int
    created_at: datetime.datetime  # Фактически, это и есть used_at

    class Config:
        from_attributes = True
