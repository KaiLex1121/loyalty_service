from pydantic import BaseModel
from typing import List

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
