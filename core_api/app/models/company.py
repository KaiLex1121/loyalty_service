from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SQLAlchemyEnum

from app.db.base import Base
from app.enums.company_enums import CompanyStatusEnum, LegalFormEnum
from app.models.company_default_cashback_config import CompanyDefaultCashbackConfig

if TYPE_CHECKING:
    from .customer_role import CustomerRole
    from .employee_role import EmployeeRole
    from .notification import NotificationMessage
    from .outlet import Outlet
    from .promotions.promotion import Promotion
    from .subscription import Subscription
    from .telegram_bot import TelegramBot
    from .transaction import Transaction
    from .user_role import UserRole
    from .telegram_bot import TelegramBot


class Company(Base):
    __tablename__ = "companies"
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    owner_user_role_id: Mapped[int] = mapped_column(
        ForeignKey("user_roles.id", ondelete="CASCADE"), nullable=False
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
    legal_form: Mapped[LegalFormEnum] = mapped_column(
        SQLAlchemyEnum(
            LegalFormEnum,
            name="legal_form_enum",
            create_constraint=True,
            inherit_schema=True,
        ),
        nullable=False,
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
    # -----------------------------

    owner_user_role: Mapped["UserRole"] = relationship(
        "UserRole", back_populates="companies_owned"
    )
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription", back_populates="company", cascade="all, delete-orphan"
    )
    outlets: Mapped[List["Outlet"]] = relationship(
        "Outlet", back_populates="company", cascade="all, delete-orphan"
    )
    employees: Mapped[List["EmployeeRole"]] = relationship(
        "EmployeeRole", back_populates="company", cascade="all, delete-orphan"
    )
    customers: Mapped[List["CustomerRole"]] = relationship(
        "CustomerRole", back_populates="company", cascade="all, delete-orphan"
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
    default_cashback_config: Mapped["CompanyDefaultCashbackConfig"] = relationship(
        "CompanyDefaultCashbackConfig",
        back_populates="company",
        uselist=False,
        cascade="all, delete-orphan",
    )
    telegram_bots: Mapped[List["TelegramBot"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name='{self.name}', inn='{self.inn}')>"
