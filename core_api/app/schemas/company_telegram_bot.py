from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.enums import OtpPurposeEnum
from app.enums.telegram_bot_enums import BotTypeEnum


class TelegramBotBase(BaseModel):
    token: str = Field(..., description="Telegram Bot Token")
    bot_type: BotTypeEnum
    is_active: bool = True


class TelegramBotCreate(TelegramBotBase):
    pass


class TelegramBotCreateInternal(TelegramBotBase):
    """Схема для создания бота в БД, используется внутри сервиса и DAO."""
    company_id: int

# Схема для обновления (например, деактивации)
class TelegramBotUpdate(BaseModel):
    is_active: bool


class TelegramBotInDB(TelegramBotBase):
    id: int

    class Config:
        from_attributes = True


# Схема для ответа API
class TelegramBotResponse(TelegramBotInDB):
    class Config:
        from_attributes = True
