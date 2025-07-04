# backend/schemas/promotion.py
import datetime
import decimal
from typing import Dict, Optional

from pydantic import (
    BaseModel,
    Field,
    computed_field,
    field_validator,
    model_validator,
    validator,
)

from app.enums import PromotionStatusEnum, PromotionTypeEnum
from app.enums.loyalty_enums import PromotionPriorityLevelEnum
from app.schemas.promotion_cashback_config import (
    CashbackConfigCreate,
    CashbackConfigResponse,
    CashbackConfigUpdate,
)

PRIORITY_LEVEL_TO_INT_MAP: Dict[PromotionPriorityLevelEnum, int] = {
    PromotionPriorityLevelEnum.MINIMAL: 0,
    PromotionPriorityLevelEnum.LOW: 25,
    PromotionPriorityLevelEnum.MEDIUM: 50,
    PromotionPriorityLevelEnum.HIGH: 75,
    PromotionPriorityLevelEnum.MAXIMUM: 100,
}

INT_TO_PRIORITY_LEVEL_MAP: Dict[int, PromotionPriorityLevelEnum] = {
    v: k for k, v in PRIORITY_LEVEL_TO_INT_MAP.items()
}


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
        default=PromotionStatusEnum.ACTIVE, description="Status of the promotion"
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
    min_purchase_amount: Optional[decimal.Decimal] = Field(
        None, ge=0, examples=[1000.0]
    )
    max_uses_per_customer: Optional[int] = Field(None, ge=0, examples=[1])
    max_total_uses: Optional[int] = Field(None, ge=0, examples=[100])

    @field_validator(
        "promotion_type", mode="after"
    )  # mode='after' вызывается после стандартной валидации типа Pydantic
    @classmethod  # Валидаторы полей теперь часто определяются как classmethod
    def _check_promotion_type_mvp(
        cls, v_promo_type: PromotionTypeEnum
    ) -> PromotionTypeEnum:
        # 'v_promo_type' здесь уже будет корректного типа PromotionTypeEnum (если базовая валидация прошла)
        if v_promo_type != PromotionTypeEnum.CASHBACK:
            raise ValueError(
                "В текущей версии поддерживается только тип акции 'CASHBACK'."
            )
        return v_promo_type

    # Межполевая валидация дат с использованием @model_validator
    @model_validator(mode="after")
    def check_dates_consistency(self) -> "PromotionBase":
        if self.end_date is not None and self.start_date is not None:
            if self.end_date < self.start_date:
                raise ValueError("Дата окончания не может быть раньше даты начала.")
        return self


class PromotionCreate(PromotionBase):
    priority_level: PromotionPriorityLevelEnum = Field(
        default=PromotionPriorityLevelEnum.MEDIUM,
        description="Уровень приоритета акции",
    )
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
    priority: int  # <--- ЧИСЛОВОЕ ПОЛЕ ДЛЯ DAO


class PromotionUpdate(BaseModel):  # Все поля опциональны
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[PromotionStatusEnum] = None
    start_date: Optional[datetime.datetime] = None
    end_date: Optional[datetime.datetime] = (
        None  # Может быть установлено в None для бессрочной
    )
    priority: Optional[int] = Field(None, ge=0)
    priority_level: Optional[PromotionPriorityLevelEnum] = Field(
        None, description="Новый уровень приоритета акции"
    )
    min_purchase_amount: Optional[decimal.Decimal] = Field(None, ge=0)
    max_uses_per_customer: Optional[int] = Field(None, ge=0)
    max_total_uses: Optional[int] = Field(None, ge=0)

    cashback_config: Optional[CashbackConfigUpdate] = None


class PromotionResponse(PromotionBase):
    id: int
    company_id: int
    priority: int
    current_total_uses: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    deleted_at: Optional[datetime.datetime] = None

    cashback_config: Optional[CashbackConfigResponse] = None

    @computed_field
    @property
    def priority_level(self) -> Optional[PromotionPriorityLevelEnum]:
        """Строковое представление уровня приоритета."""
        return INT_TO_PRIORITY_LEVEL_MAP.get(self.priority)

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

    @computed_field
    @property
    def priority_level(self) -> Optional[PromotionPriorityLevelEnum]:
        """Строковое представление уровня приоритета."""
        return INT_TO_PRIORITY_LEVEL_MAP.get(self.priority)

    class Config:
        from_attributes = True
