import datetime
import decimal
from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import (JSON, Boolean, DateTime, ForeignKey, Numeric, String,
                        Text, Time)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base  # Ваш базовый класс

if TYPE_CHECKING:
    from .company import Company
    from .transaction import Transaction


class Promotion(Base):
    __tablename__ = "promotions"

    name: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cashback_percentage: Mapped[decimal.Decimal] = mapped_column(Numeric(5, 2))
    start_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))

    days_of_week: Mapped[Optional[List[int]]] = mapped_column(
        JSON, nullable=True
    )  # Например, [0, 1, 6]
    start_time: Mapped[Optional[datetime.time]] = mapped_column(
        Time(timezone=True), nullable=True
    )
    end_time: Mapped[Optional[datetime.time]] = mapped_column(
        Time(timezone=True), nullable=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(default=0)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE")
    )

    # Связи
    company: Mapped["Company"] = relationship(back_populates="promotions")
    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="applied_promotion"
    )

    def __repr__(self) -> str:
        return f"<Promotion(id={self.id}, name='{self.name}')>"
