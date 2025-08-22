import datetime
import decimal
from typing import Optional

from app.enums import PaymentCycleEnum, SubscriptionStatusEnum
from app.schemas.company_tariff_plan import TariffPlanResponseForCompany
from pydantic import BaseModel


class SubscriptionBase(BaseModel):
    status: SubscriptionStatusEnum
    start_date: datetime.date
    end_date: Optional[datetime.date] = None
    trial_end_date: Optional[datetime.date] = None
    next_billing_date: Optional[datetime.date] = None
    auto_renew: bool = False


class SubscriptionCreate(SubscriptionBase):  # Для внутреннего использования сервисом
    company_id: int
    tariff_plan_id: int
    # current_price и current_billing_cycle могут быть установлены здесь, если нужно переопределить тариф
    current_price: Optional[decimal.Decimal] = None
    current_billing_cycle: Optional[PaymentCycleEnum] = None


class SubscriptionResponse(SubscriptionBase):
    id: int
    company_id: int
    tariff_plan_id: int
    # Можно добавить информацию о тарифе для удобства
    # tariff_plan_name: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class SubscriptionResponseForCompany(BaseModel):
    id: int
    status: SubscriptionStatusEnum
    next_billing_date: Optional[datetime.date]
    auto_renew: bool
    tariff_plan: Optional[TariffPlanResponseForCompany]

    class Config:
        from_attributes = True
