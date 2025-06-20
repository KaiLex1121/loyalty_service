import datetime
import decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base
from backend.enums import PromotionStatusEnum, PromotionTypeEnum

if TYPE_CHECKING:
    from backend.models.company import Company
    from backend.models.promotions.cashback_config import CashbackConfig
    from backend.models.promotions.promotion_usage import PromotionUsage


class Promotion(Base):
    __tablename__ = "promotions"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", name="fk_promotions_company_id_companies"),
        nullable=False,
        index=True,
    )
    company: Mapped["Company"] = relationship(back_populates="promotions")

    promotion_type: Mapped[PromotionTypeEnum] = mapped_column(
        PGEnum(
            PromotionTypeEnum, name="promotion_type_enum", create_type=True
        ),  # create_type=True для Alembic
        nullable=False,
        default=PromotionTypeEnum.CASHBACK,  # По умолчанию CASHBACK для MVP
        server_default=PromotionTypeEnum.CASHBACK.value,
    )
    status: Mapped[PromotionStatusEnum] = mapped_column(
        PGEnum(PromotionStatusEnum, name="promotion_status_enum", create_type=True),
        nullable=False,
        default=PromotionStatusEnum.DRAFT,
        server_default=PromotionStatusEnum.DRAFT.value,
        index=True,
    )

    start_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_date: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # Может быть бессрочной (для базовой)

    priority: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0", index=True
    )  # 0 - самый низкий

    is_base_for_company: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false", index=True
    )  # Базовый кэшбэк для компании?

    min_purchase_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )

    # Ограничения использования (MVP - опционально, но полезно оставить)
    max_uses_per_customer: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # потребует PromotionUsage
    max_total_uses: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # потребует PromotionUsage и счетчика в Promotion
    current_total_uses: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )  # Счетчик для max_total_uses

    # Связи
    cashback_config: Mapped[Optional["CashbackConfig"]] = relationship(
        "CashbackConfig",
        back_populates="promotion",
        uselist=False,  # Один-к-одному
        cascade="all, delete-orphan",  # При удалении акции удалять и ее конфиг
    )
    usages: Mapped[List["PromotionUsage"]] = relationship(
        "PromotionUsage",
        back_populates="promotion",
        cascade="all, delete-orphan",  # При удалении акции удалять и записи об использовании
    )
    # gift_config: Mapped[Optional["GiftConfig"]] = relationship(...) # MVP - отложено
    # points_config: Mapped[Optional["PointsMultiplierConfig"]] = relationship(...) # MVP - отложено
    # product_filters: Mapped[List["PromotionProductFilter"]] = relationship(...) # MVP - отложено

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "is_base_for_company",
            name="uq_company_base_promotion_if_true",
            postgresql_where=Column("is_base_for_company"),
        ),
        # Можно добавить UniqueConstraint('company_id', 'name', name='uq_promotion_company_name') если имена акций должны быть уникальны в рамках компании
    )

    def __repr__(self) -> str:
        return f"<Promotion(id={self.id}, name='{self.name}', company_id={self.company_id}, type='{self.promotion_type.value}')>"
