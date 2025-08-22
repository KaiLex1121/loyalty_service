import decimal
from typing import TYPE_CHECKING, Optional

from app.db.base import Base
from sqlalchemy import Boolean, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.company import Company


class CompanyDefaultCashbackConfig(Base):
    __tablename__ = "company_default_cashback_configs"

    company_id: Mapped[int] = mapped_column(
        ForeignKey(
            "companies.id",
            name="fk_comp_def_cash_conf_comp_id_companies",
            ondelete="CASCADE",
        ),
        unique=True,
        nullable=False,
        index=True,
    )
    company: Mapped["Company"] = relationship(back_populates="default_cashback_config")

    default_percentage: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 2), nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    def __repr__(self) -> str:
        return (
            f"<CompanyDefaultCashbackConfig(id={self.id}, "
            f"company_id={self.company_id}, percentage={self.default_percentage}, "
            f"is_active={self.is_active})>"
        )
