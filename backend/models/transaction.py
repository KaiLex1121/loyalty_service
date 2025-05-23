import datetime
import decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.db.base import Base

if TYPE_CHECKING:
    from .company import Company
    from .customer_role import CustomerRole
    from .outlet import Outlet
    from .promotion import Promotion


class Transaction(Base):
    __tablename__ = "transactions"

    purchase_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(10, 2), default=decimal.Decimal("0.00"), nullable=False
    )
    cashback_accrued: Mapped[decimal.Decimal] = mapped_column(
        Numeric(10, 2), default=decimal.Decimal("0.00"), nullable=False
    )
    cashback_spent: Mapped[decimal.Decimal] = mapped_column(
        Numeric(10, 2), default=decimal.Decimal("0.00"), nullable=False
    )
    transaction_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    balance_after: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(12, 2), nullable=True) # Для аудита

    customer_role_id: Mapped[int] = mapped_column(
        ForeignKey("customer_roles.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    outlet_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("outlets.id", ondelete="SET NULL"), nullable=True
    )
    applied_promotion_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("promotions.id", ondelete="SET NULL"), nullable=True
    )

    customer_role_profile: Mapped["CustomerRole"] = relationship(
        "CustomerRole", back_populates="transactions"
    )
    company: Mapped["Company"] = relationship("Company", back_populates="transactions")
    outlet: Mapped[Optional["Outlet"]] = relationship(
        "Outlet", back_populates="transactions"
    )
    applied_promotion: Mapped[Optional["Promotion"]] = relationship(
        "Promotion", back_populates="transactions"
    )  # Добавил back_populates

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, customer_role_id={self.customer_role_id}, amount={self.purchase_amount})>"
