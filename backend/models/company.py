from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base  # Ваш базовый класс

if TYPE_CHECKING:
    from .cashback_config import CashbackConfig
    from .customer import Customer
    from .employee import Employee
    from .notification import NotificationMessage
    from .outlet import Outlet
    from .promotion import Promotion
    from .transaction import Transaction
    from .user import User


class Company(Base):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String, index=True)
    legal_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    inn: Mapped[str] = mapped_column(String, unique=True, index=True)
    ogrn: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    requisites: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    # Связи
    owner: Mapped["User"] = relationship(back_populates="companies")

    outlets: Mapped[List["Outlet"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    employees: Mapped[List["Employee"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    cashback_config: Mapped[Optional["CashbackConfig"]] = relationship(
        back_populates="company", uselist=False, cascade="all, delete-orphan"
    )
    promotions: Mapped[List["Promotion"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    customers: Mapped[List["Customer"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    notification_messages: Mapped[List["NotificationMessage"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name='{self.name}', inn='{self.inn}')>"
