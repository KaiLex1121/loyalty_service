from typing import List, Literal, Optional

from pydantic import BaseModel

from shared.enums.telegram_bot_enums import BotTypeEnum


class BroadcastTask(BaseModel):
    """Задача на рассылку, передаваемая через брокер."""

    broadcast_id: int
    bot_token: str
    user_ids: List[int]
    message_text: str


class BotInfo(BaseModel):
    """Информация о боте для внутреннего использования."""

    token: str
    company_id: int
    company_name: str
    bot_type: BotTypeEnum


class BotManagementEvent(BaseModel):
    event_type: Literal[
        "bot_created", "bot_activated", "bot_deactivated", "bot_deleted"
    ]
    token: str
    webhook_url: str | None = None


class TokenPayload(BaseModel):
    sub: str
    exp: int

    scopes: List[str] = []  # Например, ["client"] или ["backoffice_admin"]
    company_id: Optional[int] = (
        None  # Для клиентского токена, чтобы знать контекст компании
    )
    account_id: Optional[int] = None  # Для клиентского токена, ID связанного Account
    outlet_id: Optional[int] = None  # Для работника, ID связанного Outlet
