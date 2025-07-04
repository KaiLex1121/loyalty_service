import datetime
import decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.customer_role import CustomerRole
    from app.models.promotions.promotion import Promotion
    from app.models.transaction import Transaction


class PromotionUsage(Base):
    __tablename__ = "promotion_usages"

    promotion_id: Mapped[int] = mapped_column(
        ForeignKey(
            "promotions.id",
            name="fk_promotion_usages_promotion_id_promotions",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    promotion: Mapped["Promotion"] = relationship(back_populates="usages")

    customer_role_id: Mapped[int] = mapped_column(
        ForeignKey(
            "customer_roles.id",
            name="fk_promotion_usages_customer_role_id_customer_roles",
        ),
        nullable=False,
        index=True,
    )
    customer_role: Mapped["CustomerRole"] = (
        relationship()
    )  # Добавьте back_populates в CustomerRole, если нужно

    transaction_id: Mapped[Optional[int]] = (
        mapped_column(  # Связь с транзакцией, где была применена акция
            ForeignKey(
                "transactions.id",
                name="fk_promotion_usages_transaction_id_transactions",
            ),
            nullable=False,
            unique=True,
        )
    )
    transaction: Mapped[Optional["Transaction"]] = relationship(
        back_populates="promotion_usage_entry"
    )

    cashback_accrued: Mapped[decimal.Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )

    __table_args__ = (
        # Гарантирует, что конкретная акция применена к конкретной транзакции только один раз.
        # Если одна и та же акция может быть применена к транзакции несколько раз (например, для разных товаров в чеке,
        # и каждая строка - отдельное применение), то этот констрейнт нужно убрать или модифицировать.
        # Для MVP кэшбэка на весь чек - этот констрейнт подходит.
        UniqueConstraint(
            "promotion_id", "transaction_id", name="uq_promotion_transaction_usage"
        ),
        # Если отслеживаем max_uses_per_customer, то нужен индекс для быстрого подсчета
        # Index('ix_promotion_usage_customer_promotion', 'customer_role_id', 'promotion_id'),
    )

    def __repr__(self) -> str:
        return f"<PromotionUsage(id={self.id}, promotion_id={self.promotion_id}, customer_role_id={self.customer_role_id}, transaction_id={self.transaction_id})>"


# Таблица для накопительного прогресса клиентов
class CustomerPromotionProgress(Base):
    __tablename__ = "customer_promotion_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    promotion_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("promotions.id"), nullable=False
    )

    # Текущий прогресс
    current_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_purchase_date: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Количество завершенных циклов (для повторяющихся акций)
    completed_cycles: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    __table_args__ = (
        UniqueConstraint(
            "customer_id", "promotion_id", name="uq_customer_promotion_progress"
        ),
    )
