import datetime
import decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from backend.enums.back_office import CurrencyEnum, PaymentCycleEnum, TariffStatusEnum


class TariffPlanBase(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: Optional[str] = None
    price: decimal.Decimal = Field(ge=decimal.Decimal("0.00"))
    currency: CurrencyEnum = CurrencyEnum.RUB
    billing_period: PaymentCycleEnum = PaymentCycleEnum.MONTHLY

    max_outlets: Optional[int] = Field(0, ge=0)
    max_employees: Optional[int] = Field(0, ge=0)
    max_active_promotions: Optional[int] = Field(0, ge=0)
    features: Optional[List[str]] = Field(default_factory=list)

    status: TariffStatusEnum = TariffStatusEnum.ACTIVE
    is_public: bool = True
    is_trial: bool = False
    trial_duration_days: Optional[int] = Field(None, ge=1)
    sort_order: int = 0


class TariffPlanCreate(TariffPlanBase):
    pass


class TariffPlanUpdate(BaseModel):  # Все поля опциональны для обновления
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = None
    price: Optional[decimal.Decimal] = Field(None, ge=decimal.Decimal("0.00"))
    currency: Optional[CurrencyEnum] = None
    billing_period: Optional[PaymentCycleEnum] = None
    max_outlets: Optional[int] = Field(None, ge=0)
    max_employees: Optional[int] = Field(None, ge=0)
    max_active_promotions: Optional[int] = Field(None, ge=0)
    features: Optional[List[str]] = None
    status: Optional[TariffStatusEnum] = None
    is_public: Optional[bool] = None
    trial_duration_days: Optional[int] = Field(None, ge=1)
    sort_order: Optional[int] = None


class TariffPlanResponse(TariffPlanBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    # deleted_at: Optional[datetime.datetime] # Обычно не показываем

    class Config:
        from_attributes = True
