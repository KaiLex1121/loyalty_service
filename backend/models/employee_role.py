from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base
from backend.models.association_tables import employee_role_outlet_association

if TYPE_CHECKING:
    from .account import Account
    from .company import Company
    from .outlet import Outlet
    from .transaction import Transaction


class EmployeeRole(Base):
    __tablename__ = "employee_roles"

    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    position: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    performed_transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="performed_by_employee",
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    account: Mapped["Account"] = relationship(
        "Account", back_populates="employee_profile"
    )
    company: Mapped["Company"] = relationship("Company", back_populates="employees")
    assigned_outlets: Mapped[List["Outlet"]] = relationship(
        "Outlet",
        secondary=employee_role_outlet_association,
        back_populates="assigned_employee_roles",
    )

    def __repr__(self) -> str:
        return f"<EmployeeRole(id={self.id}, account_id={self.account_id}, company_id={self.company_id})>"
