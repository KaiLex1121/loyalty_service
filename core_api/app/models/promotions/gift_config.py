import datetime
import decimal
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
)
from sqlalchemy import Enum as SqlAlchemyEnum
from sqlalchemy import (
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.enums.loyalty_enums import GiftTypeEnum

if TYPE_CHECKING:
    from app.models.promotions.promotion import Promotion


class GiftConfig(Base):
    __tablename__ = "gift_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    promotion_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("promotions.id"), nullable=False, unique=True
    )

    gift_type: Mapped[GiftTypeEnum] = mapped_column(
        SqlAlchemyEnum(GiftTypeEnum), nullable=False
    )

    # Для "каждый N-й товар бесплатно"
    nth_item: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Для "купи X получи Y"
    buy_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    get_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Для накопительных акций
    accumulation_target: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Для подарка за сумму
    threshold_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    # Описание подарка
    gift_description: Mapped[str] = mapped_column(String(500), nullable=False)

    # ID продукта-подарка (если это конкретный товар)
    gift_product_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    promotion: Mapped["Promotion"] = relationship(
        "Promotion", back_populates="gift_config"
    )
