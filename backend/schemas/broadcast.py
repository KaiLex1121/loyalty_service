from datetime import datetime

from pydantic import BaseModel, Field

from backend.enums.telegram_bot_enums import BroadcastStatusEnum


class BroadcastCreateRequest(BaseModel):
    message_text: str = Field(..., min_length=1, max_length=4096)


class BroadcastResponse(BaseModel):
    id: int
    message_text: str
    status: BroadcastStatusEnum
    sent_count: int
    failed_count: int
    company_id: int
    created_at: datetime

    class Config:
        from_attributes = True
