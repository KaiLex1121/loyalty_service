from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from backend.utils.validators import RussianPhoneNumber


class AccountBase(BaseModel):
    phone_number: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: bool = False


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    hashed_password: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class AccountCreateInternal(AccountBase):
    hashed_password: str


class AccountCreateForClientOnboarding(BaseModel):
    phone_number: RussianPhoneNumber
    full_name: Optional[str] = None
    telegram_user_id: int
    is_active: bool = True
    telegram_username: Optional[str] = None


class AccountInDBBase(BaseModel):
    """
    Базовая схема для представления OTP кода, как он есть в базе данных,
    включая поля, унаследованные от вашей Base SQLAlchemy модели.
    """

    id: int
    phone_number: str
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AccountResponse(AccountInDBBase):
    """
    Схема Account для ответа API. Ha данный момент совпадает c AccountInDBBase, но можно расширить
    """

    # customer_roles: List[CustomerRoleInAccountResponse] = []
    # employee_role: EmployeeRoleInAccountResponse = None
    # user_role: UserRoleInAccountResponse = None


class AccountResponseForEmployee(AccountInDBBase):
    id: int

    class Config:
        from_attributes = True
