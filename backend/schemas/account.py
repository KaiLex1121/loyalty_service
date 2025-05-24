from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class AccountBase(BaseModel):
    phone_number: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: bool = False


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


# Базовая схема для ответа API, содержащая общие поля Account
class AccountInDBBase(BaseModel):
    id: int
    phone_number: str
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: bool
    created_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Полная схема Account для ответа API. На данный момент совпадает с AccountInDBBase, но можно расширить
class Account(AccountInDBBase):
    pass
