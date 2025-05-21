from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base

if TYPE_CHECKING:
    from .account import Account
    from .company import Company
    from .outlet import Outlet

# Ассоциативная таблица для связи EmployeeRole <-> Outlet
# Важно: Имена колонок в FK должны соответствовать именам таблиц и колонок, на которые они ссылаются.
# Имя таблицы "employee_roles" и "outlets". PK в них "id".
employee_role_outlet_association = Table(
    "employee_role_outlet_association",  # Имя таблицы связи
    Base.metadata,
    Column(
        "employee_role_id",
        BigInteger,
        ForeignKey("employee_roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "outlet_id",
        BigInteger,
        ForeignKey("outlets.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class EmployeeRole(Base):
    __tablename__ = "employee_roles"

    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    position: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )  # Сотрудник привязан к компании

    account: Mapped["Account"] = relationship(
        "Account", back_populates="employee_profile"
    )
    company: Mapped["Company"] = relationship(
        "Company", back_populates="employee_roles"
    )

    assigned_outlets: Mapped[List["Outlet"]] = relationship(
        "Outlet",  # Целевая модель
        secondary=employee_role_outlet_association,  # Таблица связи
        back_populates="assigned_employee_roles",  # Атрибут в Outlet
    )

    def __repr__(self) -> str:
        return f"<EmployeeRole(id={self.id}, account_id={self.account_id}, company_id={self.company_id})>"
