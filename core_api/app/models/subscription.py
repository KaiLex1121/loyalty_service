import datetime
import decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SQLAlchemyEnum

from app.db.base import Base
from app.enums import PaymentCycleEnum, SubscriptionStatusEnum

if TYPE_CHECKING:
    from .company import Company
    from .tariff_plan import TariffPlan


class Subscription(Base):
    __tablename__ = "subscriptions"

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tariff_plan_id: Mapped[int] = mapped_column(
        ForeignKey("tariff_plans.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    status: Mapped[SubscriptionStatusEnum] = mapped_column(
        SQLAlchemyEnum(
            SubscriptionStatusEnum,
            name="subscription_status_enum",
            create_constraint=True,
            inherit_schema=True,
        ),
        nullable=False,
        index=True,
        default=SubscriptionStatusEnum.TRIALING,
    )

    start_date: Mapped[datetime.date] = mapped_column(
        Date, nullable=False
    )  # Дата начала действия этой подписки
    end_date: Mapped[Optional[datetime.date]] = mapped_column(
        Date, nullable=True
    )  # Дата окончания (если не бессрочная или отменена)
    trial_end_date: Mapped[Optional[datetime.date]] = mapped_column(
        Date, nullable=True
    )  # Если это триал, дата его окончания
    next_billing_date: Mapped[Optional[datetime.date]] = mapped_column(
        Date, nullable=True, index=True
    )  # Дата следующего списания
    current_price: Mapped[Optional[decimal.Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )  # Это поле позволяет переопределить стандартную цену тарифа для конкретной подписки.
    # Оно хранит индивидуальную цену, по которой компания оплачивает данный тариф в рамках этой конкретной подписки
    current_billing_cycle: Mapped[Optional[PaymentCycleEnum]] = mapped_column(
        SQLAlchemyEnum(
            PaymentCycleEnum,
            name="subscription_payment_cycle_enum",
            create_constraint=False,
            inherit_schema=True,
        ),
        nullable=True,
    )
    auto_renew: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )  # Автоматически продлевать подписку?
    canceled_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    company: Mapped["Company"] = relationship("Company", back_populates="subscriptions")
    tariff_plan: Mapped["TariffPlan"] = relationship(
        "TariffPlan", back_populates="subscriptions"
    )

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, company_id={self.company_id}, tariff_plan_id={self.tariff_plan_id}, status='{self.status.value}')>"

    # Свойство для получения актуальной цены (из подписки или тарифа)
    @property
    def active_price(self) -> Optional[decimal.Decimal]:
        if self.current_price is not None:
            return self.current_price
        if self.tariff_plan:
            return self.tariff_plan.default_price
        return None

    # Свойство для получения актуального биллингового цикла
    @property
    def active_billing_cycle(self) -> Optional[PaymentCycleEnum]:
        if self.current_billing_cycle is not None:
            return self.current_billing_cycle
        if self.tariff_plan:
            return self.tariff_plan.billing_period
        return None
