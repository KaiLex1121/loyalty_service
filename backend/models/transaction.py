import datetime
import decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.db.base import Base  # Ваш базовый класс

if TYPE_CHECKING:
    from .company import Company
    from .customer import Customer
    from .outlet import Outlet
    from .promotion import Promotion


class Transaction(Base):
    __tablename__ = "transactions"

    purchase_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(10, 2), default=decimal.Decimal("0.00")
    )
    cashback_accrued: Mapped[decimal.Decimal] = mapped_column(
        Numeric(10, 2), default=decimal.Decimal("0.00")
    )
    cashback_spent: Mapped[decimal.Decimal] = mapped_column(
        Numeric(10, 2), default=decimal.Decimal("0.00")
    )
    transaction_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE")
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE")
    )
    outlet_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("outlets.id", ondelete="SET NULL"), nullable=True
    )
    applied_promotion_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("promotions.id", ondelete="SET NULL"), nullable=True
    )

    # Связи
    customer: Mapped["Customer"] = relationship(back_populates="transactions")
    company: Mapped["Company"] = relationship(back_populates="transactions")
    outlet: Mapped[Optional["Outlet"]] = relationship(back_populates="transactions")
    applied_promotion: Mapped[Optional["Promotion"]] = relationship(
        back_populates="transactions"
    )

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, customer_id={self.customer_id}, amount={self.purchase_amount})>"
