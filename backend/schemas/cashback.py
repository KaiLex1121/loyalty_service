from pydantic import BaseModel
import decimal

class CashbackConfigBase(BaseModel):
    default_percentage: decimal.Decimal
    is_active: bool = True


class CashbackConfigCreate(CashbackConfigBase):
    company_id: int # Будет установлено в сервисе


class CashbackConfigResponse(CashbackConfigBase):
    id: int
    company_id: int

    class Config:
        from_attributes = True
