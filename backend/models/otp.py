import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String  # Integer для id
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Enum as SQLAlchemyEnum

from backend.db.base import Base  # Ваш базовый класс
from common.enums.back_office import OtpPurposeEnum

if TYPE_CHECKING:
    from .account import Account


class OtpCode(Base):
    __tablename__ = "otp_codes"

    code: Mapped[str] = mapped_column(String(10), nullable=False)
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    otp_type: Mapped[OtpPurposeEnum] = mapped_column(
        SQLAlchemyEnum(
            OtpPurposeEnum,
            name="otp_type_enum",
            create_constraint=True,
            inherit_schema=True,
        ),
        nullable=False,
        default=OtpPurposeEnum.LOGIN,
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    channel: Mapped[str] = mapped_column(String(10))

    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    account: Mapped["Account"] = relationship("Account")

    def __repr__(self) -> str:
        return f"<OtpCode(id={self.id}, account_id={self.account_id}, used={self.is_used})>"
