import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.db.base import Base  # Ваш базовый класс

if TYPE_CHECKING:
    from .company import Company
    from .user import User


class NotificationMessage(Base):
    __tablename__ = "notification_messages"

    title: Mapped[str] = mapped_column(String)
    body: Mapped[str] = mapped_column(Text)  # Text для длинных сообщений
    target_segment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sent_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    status: Mapped[str] = mapped_column(String, default="pending")

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE")
    )
    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Связи
    company: Mapped["Company"] = relationship(back_populates="notification_messages")
    created_by_user: Mapped[Optional["User"]] = relationship(
        back_populates="created_notifications"
    )

    def __repr__(self) -> str:
        return f"<NotificationMessage(id={self.id}, title='{self.title}', company_id={self.company_id})>"
