import decimal
from typing import TYPE_CHECKING, Optional

from app.db.base import Base  # Убедитесь, что путь правильный
from app.enums import CashbackTypeEnum
from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.promotions.promotion import Promotion  # Импорт для type hinting


class CashbackConfig(Base):
    __tablename__ = "cashback_configs"  # Имя таблицы оставляем как у вас было, или можно переименовать в promotion_cashback_configs

    promotion_id: Mapped[int] = mapped_column(
        ForeignKey(
            "promotions.id",
            name="fk_cashback_configs_promotion_id_promotions",
            ondelete="CASCADE",
        ),  # ondelete CASCADE
        unique=True,  # Гарантирует, что одна акция имеет только один конфиг кэшбэка
        nullable=False,
    )
    promotion: Mapped["Promotion"] = relationship(back_populates="cashback_config")

    cashback_type: Mapped[CashbackTypeEnum] = mapped_column(
        PGEnum(CashbackTypeEnum, name="cashback_type_enum", create_type=True),
        nullable=False,
    )

    cashback_percentage: Mapped[Optional[decimal.Decimal]] = mapped_column(
        Numeric(
            5, 2
        ),  # Например, 999.99 (5 цифр, 2 после запятой). Проверьте, достаточно ли 5,2 для ваших нужд. Может быть 100.00%? Тогда (5,2) или (6,2) если >100%
        nullable=True,  # Null, если тип FIXED_AMOUNT
    )
    cashback_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True  # Сумма кэшбэка  # Null, если тип PERCENTAGE
    )

    max_cashback_per_transaction: Mapped[Optional[decimal.Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True  # Максимальная сумма кэшбэка за одну операцию
    )

    def __repr__(self) -> str:
        return f"<CashbackConfig(id={self.id}, promotion_id={self.promotion_id}, type='{self.cashback_type.value}')>"
