import datetime
import decimal
from typing import List, Optional

from app.dao import company
from app.enums import (
    CurrencyEnum,
    OutletStatusEnum,
    PaymentCycleEnum,
    TariffStatusEnum,
)
from pydantic import BaseModel, Field


class OutletBase(BaseModel):
    name: str = Field(
        min_length=3, max_length=100, description="Название торговой точки"
    )
    address: str = Field(
        min_length=3, max_length=255, description="Адрес торговой точки"
    )


class OutletCreate(OutletBase):
    pass


class OutletUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    address: Optional[str] = Field(None, min_length=3, max_length=255)
    status: Optional[OutletStatusEnum] = None


class OutletResponse(OutletBase):
    id: int
    company_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    status: OutletStatusEnum

    class Config:
        from_attributes = True


class OutletInDB(OutletResponse):
    deleted_at: Optional[datetime.datetime]


class OutletResponseForEmployee(OutletBase):
    id: int

    class Config:
        from_attributes = True
