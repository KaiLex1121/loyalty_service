from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base  # Ваш базовый класс

# employee_outlet_association будет импортирован из outlet.py при необходимости

if TYPE_CHECKING:
    from .company import Company
    from .outlet import Outlet, employee_outlet_association


class Employee(Base):
    __tablename__ = "employees"

    full_name: Mapped[str] = mapped_column(String)
    position: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(
        String, unique=True, index=True, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE")
    )

    # Связи
    company: Mapped["Company"] = relationship(back_populates="employees")

    outlets: Mapped[List["Outlet"]] = relationship(
        secondary="employee_outlet_association",  # SQLAlchemy найдет по имени таблицы
        back_populates="employees",
    )

    def __repr__(self) -> str:
        return f"<Employee(id={self.id}, full_name='{self.full_name}')>"
