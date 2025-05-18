from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class User(Base):
    __tablename__ = "users"
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    phone_number: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )  # Основной идентификатор для входа
    email: Mapped[str | None] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )  # Может быть опциональным
    hashed_password: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    otp_code: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )  # Хешированный OTP или сам OTP (если короткоживущий)
    otp_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    profile: Mapped["BusinessPartnerProfile"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"User(id={self.id!r}, phone_number={self.phone_number!r}, is_active={self.is_active!r}, is_superuser={self.is_superuser!r})"
