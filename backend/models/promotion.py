import datetime
import decimal
from typing import TYPE_CHECKING, Any, List, Optional  # Any для JSON

from sqlalchemy import (JSON, Boolean, DateTime, ForeignKey, Numeric, String,
                        Text, Time)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base

if TYPE_CHECKING:
    from .company import Company
    from .transaction import Transaction  # Для обратной связи от Transaction


class Promotion(Base):
    __tablename__ = "promotions"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cashback_percentage: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 2), nullable=False
    )
    start_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    days_of_week: Mapped[Optional[List[int]]] = mapped_column(
        JSON, nullable=True
    )  # Например, [0, 1, 6]
    start_time: Mapped[Optional[datetime.time]] = mapped_column(
        Time(timezone=True), nullable=True
    )
    end_time: Mapped[Optional[datetime.time]] = mapped_column(
        Time(timezone=True), nullable=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )

    company: Mapped["Company"] = relationship("Company", back_populates="promotions")
    # Обратная связь от транзакций, к которым была применена эта акция
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="applied_promotion"
    )

    def __repr__(self) -> str:
        return f"<Promotion(id={self.id}, name='{self.name}')>"
