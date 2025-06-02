import datetime
import decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, validator

# Если Enum'ы реэкспортируются через backend.enums.__init__.py:
from backend.enums import CurrencyEnum, PaymentCycleEnum, TariffStatusEnum

# Если нет, то прямой импорт из backend.enums.back_office
# from backend.enums.back_office import CurrencyEnum, PaymentCycleEnum, TariffStatusEnum


class TariffPlanBase(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: Optional[str] = None
    price: decimal.Decimal = Field(ge=decimal.Decimal("0.00"))  # ge=0
    currency: CurrencyEnum = CurrencyEnum.RUB
    billing_period: PaymentCycleEnum = PaymentCycleEnum.MONTHLY

    max_outlets: Optional[int] = Field(0, ge=0)
    max_employees: Optional[int] = Field(0, ge=0)
    max_active_promotions: Optional[int] = Field(0, ge=0)
    features: Optional[List[str]] = Field(default_factory=list)

    status: TariffStatusEnum = TariffStatusEnum.ACTIVE
    is_public: bool = True
    is_trial: bool = False
    trial_duration_days: Optional[int] = Field(
        None, ge=1
    )  # Должно быть > 0, если is_trial=True
    sort_order: int = 0


class TariffPlanCreate(TariffPlanBase):
    @field_validator("trial_duration_days", always=True)
    def check_trial_duration_on_create(cls, v, values):
        if values.get("is_trial") and (v is None or v < 1):
            raise ValueError(
                "Trial duration in days must be provided and positive for a trial plan."
            )
        if not values.get("is_trial") and v is not None:
            # Можно разрешить устанавливать trial_duration_days и для не триальных, если это имеет смысл
            # raise ValueError('Trial duration should only be set for trial plans.')
            pass  # Пока разрешим, но is_trial будет False
        return v

    @field_validator("price", always=True)
    def check_trial_price_on_create(cls, v, values):
        if values.get("is_trial") and v > decimal.Decimal("0.00"):
            # Логируем или просто разрешаем платные триалы
            # print(f"Warning: Creating a trial plan '{values.get('name')}' with price {v}.")
            pass
        return v


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
    # is_trial обычно не меняется для существующего тарифа, создается новый.
    # Но если нужно разрешить:
    # is_trial: Optional[bool] = None
    trial_duration_days: Optional[int] = Field(None, ge=1)
    sort_order: Optional[int] = None

    # Валидатор для trial_duration_days при обновлении, если is_trial тоже можно менять
    # @validator('trial_duration_days', always=True)
    # def check_trial_duration_on_update(cls, v, values):
    #     is_trial = values.get('is_trial') # Нужно получить is_trial из данных или из объекта в БД
    #     # Эта логика сложнее при частичном обновлении, лучше валидировать в сервисе
    #     return v


class TariffPlanResponse(TariffPlanBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    # deleted_at: Optional[datetime.datetime] # Обычно не показываем

    class Config:
        from_attributes = True
