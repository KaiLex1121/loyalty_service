import decimal
from email.policy import default
from sys import intern
from typing import TYPE_CHECKING, List, Optional

from app.db.base import Base
from app.enums import CurrencyEnum, PaymentCycleEnum, TariffStatusEnum
from sqlalchemy import JSON, Boolean, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SQLAlchemyEnum

if TYPE_CHECKING:
    from .subscription import Subscription


class TariffPlan(Base):
    __tablename__ = "tariff_plans"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    internal_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_price: Mapped[decimal.Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )  # Это стандартная, базовая цена для данного тарифного плана
    # Это та цена, которая указывается на сайте.
    currency: Mapped[CurrencyEnum] = mapped_column(
        SQLAlchemyEnum(
            CurrencyEnum,
            name="currency_enum",
            create_constraint=False,
            inherit_schema=True,
        ),
        nullable=False,
        default=CurrencyEnum.RUB,
    )
    billing_period: Mapped[PaymentCycleEnum] = mapped_column(
        SQLAlchemyEnum(
            PaymentCycleEnum,
            name="tariff_payment_cycle_enum",
            create_constraint=False,
            inherit_schema=True,
        ),
        nullable=False,
        default=PaymentCycleEnum.MONTHLY,
    )
    max_outlets: Mapped[Optional[int]] = mapped_column(
        Integer, default=0, nullable=True
    )
    max_employees: Mapped[Optional[int]] = mapped_column(
        Integer, default=0, nullable=True
    )
    max_active_promotions: Mapped[Optional[int]] = mapped_column(
        Integer, default=0, nullable=True
    )
    features: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    status: Mapped[TariffStatusEnum] = mapped_column(
        SQLAlchemyEnum(
            TariffStatusEnum,
            name="tariff_status_enum",
            create_constraint=True,
            inherit_schema=True,
        ),
        default=TariffStatusEnum.ACTIVE,
        nullable=False,
        index=True,
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription", back_populates="tariff_plan"
    )

    def __repr__(self) -> str:
        return f"<TariffPlan(id={self.id}, name='{self.name}', currency={self.currency.value})>"
