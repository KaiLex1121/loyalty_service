import decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base  # Ваш базовый класс

if TYPE_CHECKING:
    from .company import Company


class CashbackConfig(Base):
    __tablename__ = "cashback_configs"


    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), unique=True
    )

    default_percentage: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 2)
    )  # Например, 5 знаков всего, 2 после запятой
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Связь
    company: Mapped["Company"] = relationship(back_populates="cashback_config")

    def __repr__(self) -> str:
        # Убедитесь, что company_id загружен, если обращаетесь к нему до коммита
        # или если self.id используется вместо company_id в __repr__
        return f"<CashbackConfig(id={self.id}, company_id={getattr(self, 'company_id', None)}, percentage={self.default_percentage})>"
