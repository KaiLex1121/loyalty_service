# app/models/notification.py
import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.db.base import Base

if TYPE_CHECKING:
    from .company import Company
    from .user_role import UserRole


class NotificationMessage(Base):
    __tablename__ = "notification_messages"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    target_segment: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sent_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    created_by_user_role_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("user_roles.id", ondelete="SET NULL"), nullable=True
    )

    company: Mapped["Company"] = relationship(
        "Company", back_populates="notification_messages"
    )
    created_by_user_role: Mapped[Optional["UserRole"]] = relationship(
        "UserRole", back_populates="created_notifications"
    )

    def __repr__(self) -> str:
        return f"<NotificationMessage(id={self.id}, title='{self.title}', company_id={self.company_id})>"
