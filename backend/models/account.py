from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base

if TYPE_CHECKING:
    from .customer_role import CustomerRole
    from .employee_role import EmployeeRole
    from .otp_code import OtpCode
    from .user_role import UserRole


class Account(Base):
    __tablename__ = "accounts"

    phone_number: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    telegram_user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, unique=True, nullable=True, index=True
    )
    telegram_username: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, index=True
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
    customer_profiles: Mapped[Optional[List["CustomerRole"]]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )

    otp_codes: Mapped[List["OtpCode"]] = relationship(
        "OtpCode", back_populates="account", cascade="all, delete-orphan"
    )
