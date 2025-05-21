from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base

# Ассоциативная таблица employee_role_outlet_association импортируется из employee_role.py

if TYPE_CHECKING:
    from .company import Company
    from .employee_role import EmployeeRole  # Импорт ассоциативной таблицы
    from .employee_role import employee_role_outlet_association
    from .transaction import Transaction


class Outlet(Base):
    __tablename__ = "outlets"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )

    company: Mapped["Company"] = relationship("Company", back_populates="outlets")

    assigned_employee_roles: Mapped[List["EmployeeRole"]] = relationship(
        "EmployeeRole",
        secondary="employee_role_outlet_association",  # Имя таблицы из employee_role.py
        back_populates="assigned_outlets",
    )

    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="outlet"
    )

    def __repr__(self) -> str:
        return f"<Outlet(id={self.id}, name='{self.name}')>"
