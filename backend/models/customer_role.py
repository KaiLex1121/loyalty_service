import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base

if TYPE_CHECKING:
    from .account import Account
    from .company import Company
    from .transaction import Transaction


class CustomerRole(Base):
    __tablename__ = "customer_roles"

    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    birth_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )

    company: Mapped[Optional["Company"]] = relationship(
        "Company", back_populates="customer_roles_profiles"
    )
    account: Mapped["Account"] = relationship(
        "Account", back_populates="customer_profile"
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="customer_role_profile",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<CustomerRole(id={self.id}, account_id={self.account_id})>"
