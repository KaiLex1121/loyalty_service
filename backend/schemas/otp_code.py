from datetime import datetime

from pydantic import BaseModel

from backend.enums.back_office import OtpPurposeEnum


class OtpCodeBase(BaseModel):
    hashed_code: str
    expires_at: datetime
    purpose: OtpPurposeEnum
    account_id: int
    channel: str


class OtpCodeCreate(OtpCodeBase):
    pass


class OtpCodeUpdate(OtpCodeBase):
    hashed_code: str | None = None
    expires_at: datetime | None = None
    purpose: OtpPurposeEnum | None = None
    account_id: int | None = None


class OtpCodeResponse(OtpCodeBase):
    id: int
    is_used: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OtpCodeInDBBase(OtpCodeResponse):
    pass
