from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base
from backend.models.promotions.promotion import Promotion


class PromotionProductFilter(Base):
    __tablename__ = "promotion_product_filters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    promotion_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("promotions.id"), nullable=False
    )

    # Фильтры по товарам
    product_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    brand_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Включить или исключить
    include: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    promotion: Mapped["Promotion"] = relationship(
        "Promotion", back_populates="product_filters"
    )
