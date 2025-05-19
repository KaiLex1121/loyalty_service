import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base  # Ваш базовый класс

if TYPE_CHECKING:
    from .company import Company
    from .transaction import Transaction


class Customer(Base):
    __tablename__ = "customers"

    phone_number: Mapped[str] = mapped_column(String, unique=True, index=True)

    first_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    birth_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)

    device_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    company_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )

    # Связи
    company: Mapped[Optional["Company"]] = relationship(
        back_populates="customers"
    )  # Optional если company_id nullable
    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, phone_number='{self.phone_number}')>"
