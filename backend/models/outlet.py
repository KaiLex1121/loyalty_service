from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SQLAlchemyEnum

from backend.db.base import Base
from backend.enums.back_office import OutletStatusEnum
from backend.models.association_tables import employee_role_outlet_association

if TYPE_CHECKING:
    from .company import Company
    from .employee_role import EmployeeRole
    from .transaction import Transaction


class Outlet(Base):
    __tablename__ = "outlets"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[OutletStatusEnum] = mapped_column(
        SQLAlchemyEnum(
            OutletStatusEnum,
            name="outlet_status_enum",
            create_constraint=True,
            inherit_schema=True,
        ),
        default=OutletStatusEnum.ACTIVE,
        nullable=False,
        index=True,
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )

    company: Mapped["Company"] = relationship("Company", back_populates="outlets")

    assigned_employee_roles: Mapped[List["EmployeeRole"]] = relationship(
        "EmployeeRole",
        secondary=employee_role_outlet_association,
        back_populates="assigned_outlets",
    )

    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="outlet"
    )

    def __repr__(self) -> str:
        return f"<Outlet(id={self.id}, name='{self.name}')>"
