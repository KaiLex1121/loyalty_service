from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class AccountBase(BaseModel):
    phone_number: str
    email: Optional[EmailStr] = None
    is_active: bool = False
    is_superAccount: bool = False


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_superAccount: Optional[bool] = None
    otp_code: Optional[str] = None
    otp_expires_at: Optional[datetime] = None


class AccountInDBBase(AccountBase):
    id: int
    otp_code: Optional[str] = None
    otp_expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Account(AccountInDBBase):  # Схема для отдачи пользователю (без otp_code)
    otp_code: Optional[str] = Field(None, exclude=True)
    otp_expires_at: Optional[datetime] = Field(None, exclude=True)
