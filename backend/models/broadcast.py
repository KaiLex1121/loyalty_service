import enum

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base
from backend.enums.telegram_bot_enums import BroadcastStatusEnum


class Broadcast(Base):
    __tablename__ = "broadcasts"

    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[BroadcastStatusEnum] = mapped_column(
        SQLAlchemyEnum(BroadcastStatusEnum, name="broadcast_status_enum"),
        default=BroadcastStatusEnum.PENDING,
        nullable=False,
    )
    sent_count: Mapped[int] = mapped_column(default=0)
    failed_count: Mapped[int] = mapped_column(default=0)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
