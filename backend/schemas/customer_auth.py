# backend/schemas/client_auth.py
import datetime
import decimal  # Для CustomerProfileResponse
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, constr

from backend.schemas.auth import PhoneNumber


# --- Схема для запроса от Telegram-бота ---
class ClientTelegramOnboardingRequest(PhoneNumber):
    telegram_user_id: int = Field(
        examples=[123456789],
        description="Уникальный ID пользователя в Telegram (если передается).",
    )
    telegram_username: Optional[str] = Field(
        None,
        examples=["client_tg_username"],
        description="Username пользователя в Telegram (если передается).",
    )
    full_name_from_telegram: Optional[str] = Field(
        None,
        max_length=255,
        examples=["Иван Петров из Telegram"],
        description="Полное имя из Telegram (если передается и используется для Account.full_name).",
    )
    birth_date: Optional[datetime.date] = Field(
        None,
        description="Дата рождения клиента (если передается).",
    )


class ClientAccountResponse(BaseModel):
    id: int
    phone_number: str
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: bool

    class Config:
        from_attributes = True


class CustomerProfileResponse(BaseModel):
    id: int
    account: ClientAccountResponse
    cashback_balance: decimal.Decimal = Field(default=decimal.Decimal("0.0"))
    birth_date: Optional[datetime.date] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True
