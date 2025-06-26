import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from backend.schemas.account import AccountResponseForEmployee
from backend.schemas.outlet import (  # Предполагаем, что есть такая базовая схема
    OutletResponseForEmployee,
)
from backend.utils.validators import RussianPhoneNumber


class EmployeeRoleBase(BaseModel):
    position: Optional[str] = Field(None, max_length=100)
    work_full_name: Optional[str] = Field(
        None, max_length=555, description="Полное рабочее имя сотрудника в компании"
    )
    work_phone_number: RussianPhoneNumber
    work_email: Optional[EmailStr] = Field(
        None, description="Рабочий email сотрудника в компании"
    )


class EmployeeCreate(BaseModel):  # Отдельная схема для создания
    account_phone_number: RussianPhoneNumber
    account_full_name: Optional[str] = Field(
        None, max_length=100, description="Фамилия для Account (если создается новый)"
    )
    account_email: Optional[EmailStr] = None  # Email для Account (если создается новый)

    # Данные для EmployeeRole (включая "рабочие" ФИО, email, телефон)
    position: Optional[str] = Field(None, max_length=100)
    outlet_ids: List[int] = Field(default_factory=list)


class EmployeeUpdate(BaseModel):  # Все поля опциональны
    # Данные для обновления EmployeeRole
    position: Optional[str] = Field(None, max_length=100)
    work_full_name: Optional[str] = Field(None, max_length=555)
    work_email: Optional[EmailStr] = None
    work_phone_number: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{1,14}$")

    outlet_ids: Optional[List[int]] = None


class EmployeeResponse(EmployeeRoleBase):
    id: int  # EmployeeRole ID
    company_id: int

    position: Optional[str]
    work_full_name: Optional[str] = None
    work_email: Optional[EmailStr] = None
    work_phone_number: Optional[str] = None

    account: AccountResponseForEmployee  # Вложенная информация об аккаунте
    assigned_outlets: List[OutletResponseForEmployee] = Field(default_factory=list)

    created_at: datetime.datetime
    updated_at: datetime.datetime
    deleted_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True


class EmployeeSummaryForOtpResponse(BaseModel):
    employee_role_id: int
    work_phone_number: str
    message: Optional[str] = None

    class Config:
        from_attributes = True  # Если будете создавать из модели EmployeeRole
