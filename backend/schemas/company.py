import datetime
import decimal
from typing import (
    List,
    Optional,
)

from pydantic import BaseModel, Field, field_validator

from backend.dao import cashback
from backend.enums.back_office import CompanyStatusEnum, LegalFormEnum
from backend.schemas.cashback import CashbackConfigResponse
from backend.schemas.subscription import SubscriptionResponseForCompany


class CompanyBase(BaseModel):
    name: str = Field(
        ..., description="Отображаемое название компании", min_length=1, max_length=255
    )

    # Реквизиты компании
    legal_name: str = Field(
        ..., description="Полное юридическое наименование", min_length=1, max_length=500
    )
    short_name: Optional[str] = Field(
        None, description="Краткое наименование компании", max_length=255
    )
    legal_form: LegalFormEnum = Field(..., description="Организационно-правовая форма")
    inn: str = Field(
        ...,
        description="ИНН компании",
        min_length=10,
        max_length=12,
        pattern=r"^\d{10}(\d{2})?$",
    )
    kpp: Optional[str] = Field(
        None, description="КПП компании (для юр. лиц)", pattern=r"^\d{9}$"
    )
    ogrn: Optional[str] = Field(
        None, description="ОГРН/ОГРНИП компании", pattern=r"^\d{13}(\d{2})?$"
    )
    legal_address: Optional[str] = Field(
        None, description="Юридический адрес компании", max_length=500
    )
    representative_full_name: Optional[str] = Field(
        None, description="ФИО представителя, подписывающего договор", max_length=255
    )

    # Банковские реквизиты
    bank_name: Optional[str] = Field(
        None, description="Наименование банка", max_length=255
    )
    bik: Optional[str] = Field(None, description="БИК банка", pattern=r"^\d{9}$")
    correspondent_account: Optional[str] = Field(
        None, description="Корреспондентский счет банка", pattern=r"^\d{20}$"
    )
    payment_account: Optional[str] = Field(
        None, description="Расчетный (платежный) счет компании", pattern=r"^\d{20}$"
    )  # Используем payment_account как в модели


class CompanyCreate(CompanyBase):
    initial_cashback_percentage: decimal.Decimal = Field(
        ...,
        gt=0,
        le=100,
        description="Начальный процент кэшбэка для компании (больше 0)",
    )

    @field_validator("initial_cashback_percentage")
    def percentage_must_be_valid(cls, v):
        if v <= decimal.Decimal("0") or v > decimal.Decimal(
            "100"
        ):  # Проверка на корректный диапазон
            raise ValueError(
                "Cashback percentage must be between 0 (exclusive) and 100 (inclusive)"
            )
        return v


class CompanyUpdate(CompanyBase):
    name: Optional[str] = Field(
        None, description="Отображаемое название компании", min_length=1, max_length=255
    )
    legal_name: Optional[str] = Field(
        None,
        description="Полное юридическое наименование",
        min_length=1,
        max_length=500,
    )
    short_name: Optional[str] = Field(
        None, description="Краткое наименование компании", max_length=255
    )
    legal_form: Optional[LegalFormEnum] = Field(
        None, description="Организационно-правовая форма"
    )
    kpp: Optional[str] = Field(
        None, description="КПП компании (для юр. лиц)", pattern=r"^\d{9}$"
    )
    ogrn: Optional[str] = Field(
        None, description="ОГРН/ОГРНИП компании", pattern=r"^\d{13}(\d{2})?$"
    )
    legal_address: Optional[str] = Field(
        None, description="Юридический адрес компании", max_length=500
    )
    representative_full_name: Optional[str] = Field(
        None, description="ФИО представителя, подписывающего договор", max_length=255
    )
    bank_name: Optional[str] = Field(
        None, description="Наименование банка", max_length=255
    )
    bik: Optional[str] = Field(None, description="БИК банка", pattern=r"^\d{9}$")
    correspondent_account: Optional[str] = Field(
        None, description="Корреспондентский счет банка", pattern=r"^\d{20}$"
    )
    payment_account: Optional[str] = Field(
        None, description="Расчетный (платежный) счет компании", pattern=r"^\d{20}$"
    )
    status: Optional[CompanyStatusEnum] = Field(
        None, description="Новый статус компании"
    )


class CompanyResponse(CompanyBase):
    id: int
    owner_user_role_id: int  # ID профиля владельца
    status: CompanyStatusEnum

    created_at: datetime.datetime
    updated_at: datetime.datetime
    current_subscription: Optional[SubscriptionResponseForCompany]
    cashback: Optional[CashbackConfigResponse]

    class Config:
        from_attributes = True


class CompanyInDBBase(CompanyResponse):
    pass
