import decimal
from typing import TYPE_CHECKING, Optional  # Optional нужен

from sqlalchemy import Boolean, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base

if TYPE_CHECKING:
    from .company import Company


class Cashback(Base):
    __tablename__ = "cashback"

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    default_percentage: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 2), nullable=False
    )
    company: Mapped["Company"] = relationship("Company", back_populates="cashback")

    def __repr__(self) -> str:
        return f"<CashbackConfig(id={self.id}, company_id={self.company_id}, percentage={self.default_percentage})>"
