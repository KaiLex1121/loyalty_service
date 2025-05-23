from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base

if TYPE_CHECKING:
    from .customer_role import CustomerRole
    from .employee_role import EmployeeRole
    from .otp import OtpCode
    from .user_role import UserRole


class Account(Base):
    __tablename__ = "accounts"

    phone_number: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user_profile: Mapped[Optional["UserRole"]] = relationship(
        "UserRole",
        back_populates="account",
        cascade="all, delete-orphan",
        uselist=False,
    )
    employee_profile: Mapped[Optional["EmployeeRole"]] = relationship(
        "EmployeeRole",
        back_populates="account",
        cascade="all, delete-orphan",
        uselist=False,
    )
    customer_profile: Mapped[Optional["CustomerRole"]] = relationship(
        "CustomerRole",
        back_populates="account",
        cascade="all, delete-orphan",
        uselist=False,
    )

    otp_codes: Mapped[List["OtpCode"]] = relationship(
        "OtpCode", back_populates="account", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Account(id={self.id}, phone_number='{self.phone_number}')>"
