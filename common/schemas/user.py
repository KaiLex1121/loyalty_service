from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    phone_number: str
    email: Optional[EmailStr] = None
    is_active: bool = False
    is_superuser: bool = False

class UserCreate(UserBase):
    pass # Дополнительные поля при создании, если нужны

class UserUpdate(BaseModel): # Для обновления пользователя
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    # другие поля для обновления

class UserInDBBase(UserBase):
    id: int
    otp_code: Optional[str] = None
    otp_expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True # Для SQLAlchemy v2 (orm_mode в Pydantic v1)

class User(UserInDBBase): # Схема для отдачи пользователю (без otp_code)
    otp_code: Optional[str] = Field(None, exclude=True) # Не отдаем OTP код клиенту
    otp_expires_at: Optional[datetime] = Field(None, exclude=True) # И время его жизни
