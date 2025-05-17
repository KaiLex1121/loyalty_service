from typing import Optional

from pydantic import BaseModel


class BusinessPartnerProfileBase(BaseModel):
    full_name: Optional[str] = None


class BusinessPartnerProfileCreate(BusinessPartnerProfileBase):
    pass


class BusinessPartnerProfileRead(BusinessPartnerProfileBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
