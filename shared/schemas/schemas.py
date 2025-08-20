from pydantic import BaseModel
from typing import List, Literal


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


class BotManagementEvent(BaseModel):
    event_type: Literal["bot_created", "bot_activated", "bot_deactivated", "bot_deleted"]
    token: str
    webhook_url: str | None = None
