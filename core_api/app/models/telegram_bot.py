import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.enums.telegram_bot_enums import BotTypeEnum

if TYPE_CHECKING:
    from app.models.company import Company


class TelegramBot(Base):
    __tablename__ = "telegram_bots"

    token: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        doc="Уникальный токен, выданный Telegram (BotFather)",
    )
    bot_type: Mapped[BotTypeEnum] = mapped_column(
        Enum(BotTypeEnum),
        nullable=False,
        doc="Тип бота (клиентский или для сотрудников)",
    )
    is_active: Mapped[bool] = mapped_column(default=True, doc="Флаг активности бота")

    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)

    # Связь "многие-к-одному" с компанией
    company: Mapped["Company"] = relationship(back_populates="telegram_bots")

    def __repr__(self):
        return f"Bot(token={self.token}, bot_type={self.bot_type}, is_active={self.is_active}, company_id={self.company_id})"
