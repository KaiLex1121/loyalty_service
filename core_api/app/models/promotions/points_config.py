import decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.promotions.promotion import Promotion


class PointsMultiplierConfig(Base):
    __tablename__ = "points_multiplier_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    promotion_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("promotions.id"), nullable=False, unique=True
    )

    # Множитель баллов (2.0 = двойные баллы, 3.0 = тройные и т.д.)
    multiplier: Mapped[decimal.Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    promotion: Mapped["Promotion"] = relationship(
        "Promotion", back_populates="points_config"
    )
