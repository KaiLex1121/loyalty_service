import datetime
import decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime
from sqlalchemy import Enum as PGEnum
from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.enums.loyalty_enums import TransactionStatusEnum, TransactionTypeEnum

if TYPE_CHECKING:
    from .company import Company
    from .customer_role import CustomerRole
    from .employee_role import EmployeeRole
    from .outlet import Outlet
    from .promotions.promotion import Promotion
    from .promotions.promotion_usage import PromotionUsage
    from .user_role import UserRole


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_type: Mapped[TransactionTypeEnum] = mapped_column(
        PGEnum(TransactionTypeEnum, name="transaction_type_enum", create_type=True),
        nullable=False,
        index=True,
    )
    status: Mapped[TransactionStatusEnum] = mapped_column(
        PGEnum(TransactionStatusEnum, name="transaction_status_enum", create_type=True),
        nullable=False,
        default=TransactionStatusEnum.COMPLETED,
        server_default=TransactionStatusEnum.COMPLETED.value,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    purchase_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(10, 2), default=decimal.Decimal("0.00"), nullable=False
    )
    cashback_accrued: Mapped[decimal.Decimal] = mapped_column(
        Numeric(10, 2), default=decimal.Decimal("0.00"), nullable=False
    )
    cashback_spent: Mapped[decimal.Decimal] = mapped_column(
        Numeric(10, 2), default=decimal.Decimal("0.00"), nullable=False
    )
    transaction_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    balance_after: Mapped[decimal.Decimal] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    performed_by_employee_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employee_roles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    performed_by_employee: Mapped[Optional["EmployeeRole"]] = relationship(
        "EmployeeRole", back_populates="performed_transactions"
    )
    customer_role_id: Mapped[int] = mapped_column(
        ForeignKey("customer_roles.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    outlet_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("outlets.id", ondelete="SET NULL"), nullable=True
    )
    promotion_usage_entry: Mapped[Optional["PromotionUsage"]] = relationship(
        "PromotionUsage", back_populates="transaction", uselist=False
    )

    customer_role_profile: Mapped["CustomerRole"] = relationship(
        "CustomerRole", back_populates="transactions"
    )
    company: Mapped["Company"] = relationship("Company", back_populates="transactions")
    outlet: Mapped[Optional["Outlet"]] = relationship(
        "Outlet", back_populates="transactions"
    )
    performed_by_admin_profile_id: Mapped[Optional[int]] = (
        mapped_column(  # Для ручных операций админа
            ForeignKey(
                "user_roles.id",
                name="fk_transactions_performed_by_admin_profile_id_user_roles",
            ),  # user_roles - это таблица для AdminProfile/UserRole
            nullable=True,
            index=True,
            comment="Администратор, выполнивший операцию (для ручных начислений/списаний)",
        )
    )
    performed_by_admin_profile: Mapped[Optional["UserRole"]] = relationship(
        foreign_keys=[performed_by_admin_profile_id]
    )

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, customer_role_id={self.customer_role_id}, amount={self.purchase_amount})>"
