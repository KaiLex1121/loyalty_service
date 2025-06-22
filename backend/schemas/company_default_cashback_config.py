import datetime
import decimal
from typing import Optional

from pydantic import BaseModel, Field


class CompanyDefaultCashbackConfigBase(BaseModel):
    default_percentage: decimal.Decimal = Field(
        gt=0, le=100, description="Процент кэшбэка по умолчанию (больше 0)"
    )


class CompanyDefaultCashbackConfigCreate(CompanyDefaultCashbackConfigBase):
    company_id: int


class CompanyDefaultCashbackConfigUpdate(CompanyDefaultCashbackConfigBase):
    default_percentage: Optional[decimal.Decimal] = Field(
        gt=0, le=100, description="Процент кэшбэка по умолчанию (больше 0 и менее 100)"
    )


class CompanyDefaultCashbackConfigResponse(CompanyDefaultCashbackConfigBase):
    id: int
    company_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class CompanyDefaultCashbackConfigInDB(CompanyDefaultCashbackConfigResponse):
    pass
