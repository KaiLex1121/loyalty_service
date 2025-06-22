# backend/schemas/promotion.py
import datetime
import decimal
from typing import Optional

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    root_validator,
    validator,
)

from backend.enums import PromotionStatusEnum, PromotionTypeEnum
from backend.schemas.cashback_config import (
    CashbackConfigCreate,
    CashbackConfigResponse,
    CashbackConfigUpdate,
)


class PromotionBase(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=255, examples=["Весенний кэшбэк 10%"]
    )
    description: Optional[str] = Field(
        None, examples=["Дополнительный кэшбэк на все покупки в марте"]
    )
    promotion_type: PromotionTypeEnum = Field(
        default=PromotionTypeEnum.CASHBACK,
        description="Type of the promotion (only CASHBACK for MVP)",
    )
    status: PromotionStatusEnum = Field(
        default=PromotionStatusEnum.DRAFT, description="Status of the promotion"
    )
    start_date: datetime.datetime = Field(
        ..., examples=[datetime.datetime.now(datetime.timezone.utc)]
    )
    end_date: Optional[datetime.datetime] = Field(
        None,
        examples=[
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)
        ],
    )
    priority: int = Field(
        default=0,
        ge=0,
        description="Priority of the promotion (higher value means higher priority)",
    )
    min_purchase_amount: Optional[decimal.Decimal] = Field(
        None, ge=0, examples=[1000.0]
    )
    max_uses_per_customer: Optional[int] = Field(None, ge=0, examples=[1])
    max_total_uses: Optional[int] = Field(None, ge=0, examples=[100])

    @field_validator("end_date", mode="after")
    def check_end_date_after_start_date(
        cls, v, values
    ):  # Добавил _ для Pydantic v1 совместимости, если что
        if "start_date" in values and v is not None and v < values["start_date"]:
            raise ValueError("End date must be on or after start date")
        return v

    @field_validator("promotion_type", mode="after")
    def check_promotion_type(cls, v):
        if v != PromotionTypeEnum.CASHBACK:
            raise ValueError("For MVP, only CASHBACK promotion type is supported.")
        return v


class PromotionCreate(PromotionBase):
    cashback_config: Optional[CashbackConfigCreate] = Field(
        None, description="Configuration for cashback promotion type"
    )

    @model_validator(mode="after")
    def check_config_based_on_type(cls, data):
        if (
            data.promotion_type == PromotionTypeEnum.CASHBACK
            and data.cashback_config is None
        ):
            raise ValueError("cashback_config is required for CASHBACK promotion type")
        return data


class PromotionCreateInternal(PromotionBase):  # Для внутреннего использования сервисом
    company_id: int
    current_total_uses: int = 0


class PromotionUpdate(BaseModel):  # Все поля опциональны
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[PromotionStatusEnum] = None
    start_date: Optional[datetime.datetime] = None
    end_date: Optional[datetime.datetime] = (
        None  # Может быть установлено в None для бессрочной
    )
    priority: Optional[int] = Field(None, ge=0)
    min_purchase_amount: Optional[decimal.Decimal] = Field(None, ge=0)
    max_uses_per_customer: Optional[int] = Field(None, ge=0)
    max_total_uses: Optional[int] = Field(None, ge=0)

    cashback_config: Optional[CashbackConfigUpdate] = None


class PromotionResponse(PromotionBase):
    id: int
    company_id: int
    current_total_uses: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    deleted_at: Optional[datetime.datetime] = None

    cashback_config: Optional[CashbackConfigResponse] = None

    class Config:
        from_attributes = True


class PromotionListItemResponse(BaseModel):
    id: int
    name: str
    promotion_type: PromotionTypeEnum
    status: PromotionStatusEnum
    start_date: datetime.datetime
    end_date: Optional[datetime.datetime] = None
    priority: int

    class Config:
        from_attributes = True
