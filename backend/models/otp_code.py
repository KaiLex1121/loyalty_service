import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SQLAlchemyEnum

from backend.db.base import Base
from common.enums.back_office import OtpPurposeEnum

if TYPE_CHECKING:
    from .account import Account


class OtpCode(Base):
    __tablename__ = "otp_codes"

    hashed_code: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    purpose: Mapped[OtpPurposeEnum] = mapped_column(
        SQLAlchemyEnum(
            OtpPurposeEnum,
            name="otp_purpose_enum",
            create_constraint=True,
            inherit_schema=True,
        ),
        nullable=False,
        default=OtpPurposeEnum.BACKOFFICE_LOGIN,
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    channel: Mapped[str] = mapped_column(String(10)) # Канал, по которому передается код
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    account: Mapped["Account"] = relationship("Account", back_populates="otp_codes")

    def __repr__(self) -> str:
        return f"<OtpCode(id={self.id}, account_id={self.account_id}, used={self.is_used})>"

    @property
    def is_expired(self) -> bool:
        return datetime.datetime.now(datetime.timezone.utc) > self.expires_at
