from pydantic import BaseModel


class TelegramUpdate(BaseModel):
    update_id: int
    message: str
