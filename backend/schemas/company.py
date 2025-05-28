import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, validator

from backend.enums.back_office import \
    PaymentCycleEnum  # Если используется в CompanyResponse для информации о подписке
from backend.enums.back_office import (  # Импорт из вашего enums/back_office.py
    CompanyStatusEnum, LegalFormEnum, VatTypeEnum)

# Предполагаем, что AdminAccessLevelEnum импортируется там, где нужна схема UserRole


# --- Company Schemas ---
class CompanyBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    legal_name: str = Field(..., min_length=2, max_length=500)
    inn: str = Field(
        ..., min_length=10, max_length=12, pattern=r"^\d{10}(\d{2})?$"
    )  # Валидация ИНН

    short_name: Optional[str] = Field(None, max_length=255)
    legal_form: Optional[LegalFormEnum] = None
    kpp: Optional[str] = Field(None, min_length=9, max_length=9, pattern=r"^\d{9}$")
    ogrn: Optional[str] = Field(
        None, min_length=13, max_length=15, pattern=r"^\d{13}(\d{2})?$"
    )
    okpo: Optional[str] = Field(
        None, min_length=8, max_length=10, pattern=r"^\d{8}(\d{2})?$"
    )
    okved_main: Optional[str] = Field(None, max_length=10)  # Формат XX.XX.XX
    legal_address: Optional[str] = Field(None, max_length=500)
    postal_address: Optional[str] = Field(None, max_length=500)

    representative_full_name: Optional[str] = Field(None, max_length=255)
    representative_position: Optional[str] = Field(None, max_length=255)
    representative_basis: Optional[str] = Field(None, max_length=255)
    power_of_attorney_number: Optional[str] = Field(None, max_length=50)
    power_of_attorney_date: Optional[datetime.date] = None

    bank_name: Optional[str] = Field(None, max_length=255)
    bik: Optional[str] = Field(None, min_length=9, max_length=9, pattern=r"^\d{9}$")
    correspondent_account: Optional[str] = Field(
        None, min_length=20, max_length=20, pattern=r"^\d{20}$"
    )
    checking_account: Optional[str] = Field(
        None, min_length=20, max_length=20, pattern=r"^\d{20}$"
    )

    billing_email: Optional[EmailStr] = None
    billing_phone: Optional[str] = Field(None, max_length=20)
    vat_type: Optional[VatTypeEnum] = None
    notes: Optional[str] = None


class CompanyCreateRequest(CompanyBase):
    pass  # Все поля для создания берутся из CompanyBase


class CompanyUpdateRequest(CompanyBase):
    # Делаем все поля опциональными для обновления
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    legal_name: Optional[str] = Field(None, min_length=2, max_length=500)
    inn: Optional[str] = Field(
        None, min_length=10, max_length=12, pattern=r"^\d{10}(\d{2})?$"
    )
    # ... и так далее для всех полей из CompanyBase ...
    # Статус и owner_user_role_id обычно не обновляются напрямую через этот DTO


class CompanyResponse(CompanyBase):
    id: int
    status: CompanyStatusEnum
    owner_user_role_id: int  # ID профиля владельца
    # tariff_plan_id: Optional[int] = None # Если подписка создается сразу
    # next_billing_date: Optional[datetime.date] = None # Если подписка создается сразу
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True
