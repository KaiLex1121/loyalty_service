import datetime
import decimal
from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import (JSON, Boolean,  # Добавлен Integer для tariff_plan_id
                        Date, ForeignKey, Integer, Numeric, String, Text)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SQLAlchemyEnum

from backend.db.base import Base
from common.enums.back_office import (CompanyStatusEnum, LegalFormEnum,
                                      PaymentCycleEnum, VatTypeEnum)

if TYPE_CHECKING:
    from .cashback import Cashback
    from .employee_role import EmployeeRole
    from .notification import NotificationMessage
    from .outlet import Outlet
    from .promotion import Promotion
    from .tariff_plan import TariffPlan
    from .transaction import Transaction
    from .user_role import UserRole


class Company(Base):
    __tablename__ = "companies"

    # ... (все поля до информации о тарифе) ...
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    owner_user_role_id: Mapped[int] = mapped_column(
        ForeignKey("user_roles.id", ondelete="CASCADE"), nullable=False
    )
    owner_user_role: Mapped["UserRole"] = relationship(
        "UserRole", back_populates="companies_owned"
    )
    status: Mapped[CompanyStatusEnum] = mapped_column(
        SQLAlchemyEnum(
            CompanyStatusEnum,
            name="company_status_enum",
            create_constraint=True,
            inherit_schema=True,
        ),
        default=CompanyStatusEnum.DRAFT,
        nullable=False,
        index=True,
    )

    # Реквизиты компании
    legal_name: Mapped[str] = mapped_column(String(500), nullable=False)
    short_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    legal_form: Mapped[Optional[LegalFormEnum]] = mapped_column(
        SQLAlchemyEnum(
            LegalFormEnum,
            name="legal_form_enum",
            create_constraint=True,
            inherit_schema=True,
        ),
        nullable=True,
    )
    inn: Mapped[str] = mapped_column(
        String(12), unique=True, index=True, nullable=False
    )
    kpp: Mapped[Optional[str]] = mapped_column(String(9), nullable=True)
    ogrn: Mapped[Optional[str]] = mapped_column(String(15), unique=True, nullable=True)
    legal_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    representative_full_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    # -----------------------------

    # Банковские реквизиты
    bank_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bik: Mapped[Optional[str]] = mapped_column(String(9), nullable=True)
    correspondent_account: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )
    payment_account: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    tariff_plan_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tariff_plans.id", ondelete="SET NULL"), nullable=True
    )
    next_billing_date: Mapped[Optional[datetime.date]] = mapped_column(
        Date, nullable=True
    )
    last_billing_date: Mapped[Optional[datetime.date]] = mapped_column(
        Date, nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    tariff_plan: Mapped[Optional["TariffPlan"]] = relationship(
        "TariffPlan", back_populates="companies_on_plan"
    )
    outlets: Mapped[List["Outlet"]] = relationship(
        "Outlet", back_populates="company", cascade="all, delete-orphan"
    )
    employee_roles: Mapped[List["EmployeeRole"]] = relationship(
        "EmployeeRole", back_populates="company", cascade="all, delete-orphan"
    )
    cashback: Mapped[Optional["Cashback"]] = relationship(
        "Cashback",
        back_populates="company",
        uselist=False,
        cascade="all, delete-orphan",
    )
    promotions: Mapped[List["Promotion"]] = relationship(
        "Promotion", back_populates="company", cascade="all, delete-orphan"
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="company", cascade="all, delete-orphan"
    )
    notification_messages: Mapped[List["NotificationMessage"]] = relationship(
        "NotificationMessage", back_populates="company", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name='{self.name}', inn='{self.inn}')>"
