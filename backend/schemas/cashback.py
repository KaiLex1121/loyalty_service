import decimal
from typing import Optional

from pydantic import BaseModel


class CashbackConfigBase(BaseModel):
    default_percentage: decimal.Decimal


class CashbackConfigCreate(CashbackConfigBase):
    company_id: int


class CashbackConfigUpdate(CashbackConfigBase):
    default_percentage: Optional[decimal.Decimal]


class CashbackConfigResponse(CashbackConfigBase):
    id: int

    class Config:
        from_attributes = True


class CashbackConfigInDB(CashbackConfigResponse):
    id: int
    company_id: int
