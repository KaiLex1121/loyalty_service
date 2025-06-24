# backend/schemas/customer_role.py
import datetime
import decimal
from typing import Optional

from pydantic import BaseModel, Field


# --- CustomerRole Schemas ---
class CustomerRoleBase(BaseModel):
    birth_date: Optional[datetime.date] = Field(None, examples=["1995-05-20"])


class CustomerRoleCreate(CustomerRoleBase):
    pass


class CustomerRoleUpdate(CustomerRoleBase):  # Схема для API обновления CustomerRole
    pass


class CustomerRoleCreateInternal(CustomerRoleBase):  # Схема для DAO
    account_id: int
    company_id: int
    cashback_balance: decimal.Decimal = Field(default=decimal.Decimal("0.0"))


# Схема ответа CustomerProfileResponse (которая включает CustomerRole и Account)
# уже определена в backend/schemas/client_auth.py.
# Если нужна отдельная схема только для CustomerRole:
class CustomerRoleResponse(CustomerRoleBase):
    id: int
    account_id: int
    company_id: int
    cashback_balance: decimal.Decimal
    created_at: datetime.datetime
    updated_at: datetime.datetime
    deleted_at: Optional[datetime.datetime]

    class Config:
        from_attributes = True


class CustomerBalanceResponse(BaseModel):
    """Ответ с кэшбэк балансом клиента."""

    cashback_balance: decimal.Decimal = Field(
        description="Текущий кэшбэк баланс клиента."
    )

    class Config:
        from_attributes = True
