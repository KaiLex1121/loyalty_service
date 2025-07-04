import datetime
import decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from .account import Account
    from .company import Company
    from .transaction import Transaction


class CustomerRole(Base):
    __tablename__ = "customer_roles"

    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"), nullable=False
    )
    birth_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    cashback_balance: Mapped[decimal.Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=decimal.Decimal("0.00"),
        server_default="0.00",
    )
    company: Mapped[Optional["Company"]] = relationship(
        "Company", back_populates="customers"
    )
    account: Mapped["Account"] = relationship(
        "Account", back_populates="customer_profiles"
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="customer_role_profile",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "account_id", "company_id", name="uq_customer_role_account_company"
        ),  # <--- ПРАВИЛЬНЫЙ КОНСТРЕЙНТ
    )

    def __repr__(self) -> str:
        return f"<CustomerRole(id=, account_id=)>"
