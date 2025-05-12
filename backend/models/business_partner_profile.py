from __future__ import annotations
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base



class BusinessPartnerProfile(Base):
    __tablename__ = "business_partner_profiles"

    id: Mapped[int_pk]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    full_name: Mapped[str | None] = mapped_column(String(255))
    user: Mapped["User"] = relationship(back_populates="profile")
    company: Mapped["Company"] = relationship(back_populates="business_partner", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"BusinessPartnerProfile(id={self.id!r}, user_id={self.user_id!r}, full_name={self.full_name!r})"