from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import BigInteger, Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base

if TYPE_CHECKING:
    from .company import Company
    from .notification import NotificationMessage


class User(Base):
    __tablename__ = "users"
    __mapper_args__ = {"eager_defaults": True}

    phone_number: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    email: Mapped[str | None] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    hashed_password: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    otp_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    otp_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    companies: Mapped[List["Company"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    created_notifications: Mapped[List["NotificationMessage"]] = relationship(
        back_populates="created_by_user"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, phone_number='{self.phone_number}')>"
