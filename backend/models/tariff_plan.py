import decimal
from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import (JSON, Boolean,  # Добавлены Integer, Text, JSON
                        Integer, Numeric, String, Text)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SQLAlchemyEnum

from backend.db.base import Base
from common.enums.back_office import PaymentCycleEnum, TariffStatusEnum

if TYPE_CHECKING:
    from .company import Company


class TariffPlan(Base):
    __tablename__ = "tariff_plans"

    name: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )  # Название тарифа должно быть уникальным
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    billing_period: Mapped[PaymentCycleEnum] = (
        mapped_column(  # Используем существующий PaymentCycleEnum
            SQLAlchemyEnum(
                PaymentCycleEnum,
                name="payment_cycle_enum",
                create_constraint=False,
                inherit_schema=True,
            ),  # Он уже может быть создан Company
            nullable=False,
            default=PaymentCycleEnum.MONTHLY,
        )
    )

    # Лимиты (0 или NULL означает безлимитно)
    max_outlets: Mapped[Optional[int]] = mapped_column(
        Integer, default=0, nullable=True
    )
    max_employees: Mapped[Optional[int]] = mapped_column(
        Integer, default=0, nullable=True
    )
    max_active_promotions: Mapped[Optional[int]] = mapped_column(
        Integer, default=0, nullable=True
    )

    features: Mapped[Optional[List[str]]] = mapped_column(
        JSON, nullable=True
    )  # Например: ["analytics_basic", "rfm_analysis", "push_notifications"]

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
    is_public: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )  # Виден ли всем
    is_trial: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )  # Есть ли пробный период
    trial_duration_days: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Длительность пробного периода в днях
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )  # Для сортировки при отображении
    companies_on_plan: Mapped[List["Company"]] = relationship(
        "Company", back_populates="tariff_plan"
    )

    def __repr__(self) -> str:
        return f"<TariffPlan(id={self.id}, name='{self.name}', price={self.price} {self.currency.value})>"
