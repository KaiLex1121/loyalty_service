# backend/schemas/cashback_config.py
import datetime
import decimal
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.enums import CashbackTypeEnum


# --- CashbackConfig Schemas ---
class CashbackConfigBase(BaseModel):
    cashback_type: CashbackTypeEnum
    cashback_percentage: Optional[decimal.Decimal] = Field(
        None, ge=0, le=100
    )  # Процент от 0 до 100
    cashback_amount: Optional[decimal.Decimal] = Field(None, ge=0)
    max_cashback_per_transaction: Optional[decimal.Decimal] = Field(None, ge=0)

    @model_validator(
        mode="after"
    )  # Используйте актуальный синтаксис для вашей версии Pydantic
    def check_cashback_value_based_on_type(cls, values):
        cashback_type = values.cashback_type
        cashback_percentage = values.cashback_percentage
        cashback_amount = values.cashback_amount

        if cashback_type == CashbackTypeEnum.PERCENTAGE:
            if cashback_percentage is None:
                raise ValueError("cashback_percentage is required for PERCENTAGE type")
            if cashback_amount is not None:  # Для процентного типа не должно быть суммы
                values.cashback_amount = None  # или raise ValueError("cashback_amount must be null for PERCENTAGE type")
        elif cashback_type == CashbackTypeEnum.FIXED_AMOUNT:
            if cashback_amount is None:
                raise ValueError("cashback_amount is required for FIXED_AMOUNT type")
            if (
                cashback_percentage is not None
            ):  # Для фиксированного типа не должно быть процента
                values.cashback_percentage = None  # или raise ValueError("cashback_percentage must be null for FIXED_AMOUNT type")
        return values


class CashbackConfigCreate(CashbackConfigBase):
    pass


class CashbackConfigUpdate(BaseModel):
    cashback_type: Optional[CashbackTypeEnum] = None
    cashback_percentage: Optional[decimal.Decimal] = Field(None, ge=0, le=100)
    cashback_amount: Optional[decimal.Decimal] = Field(None, ge=0)
    max_cashback_per_transaction: Optional[decimal.Decimal] = Field(None, ge=0)


class CashbackConfigResponse(CashbackConfigBase):
    id: int
    promotion_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


# Схема для внутреннего использования сервисами/DAO при создании
class CashbackConfigCreateInternal(CashbackConfigCreate):
    promotion_id: int  # Добавляется сервисом
