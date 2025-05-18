from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    phone_number: str
    email: Optional[EmailStr] = None
    is_active: bool = False
    is_superuser: bool = False


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    otp_code: Optional[str] = None
    otp_expires_at: Optional[datetime] = None


class UserInDBBase(UserBase):
    id: int
    otp_code: Optional[str] = None
    otp_expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class User(UserInDBBase):  # Схема для отдачи пользователю (без otp_code)
    otp_code: Optional[str] = Field(None, exclude=True)
    otp_expires_at: Optional[datetime] = Field(None, exclude=True)
