from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SQLAlchemyEnum

from backend.db.base import Base
from backend.enums.back_office import UserAccessLevelEnum

if TYPE_CHECKING:
    from .account import Account
    from .company import Company
    from .notification import NotificationMessage


class UserRole(Base):
    __tablename__ = "user_roles"

    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    access_level: Mapped[UserAccessLevelEnum] = mapped_column(
        SQLAlchemyEnum(
            UserAccessLevelEnum,
            name="admin_access_level_enum",
            create_constraint=True,
            inherit_schema=True,
        ),
        default=UserAccessLevelEnum.COMPANY_OWNER,
        nullable=False,
    )
    account: Mapped["Account"] = relationship("Account", back_populates="user_profile")
    companies_owned: Mapped[List["Company"]] = relationship(
        "Company", back_populates="owner_user_role"
    )
    created_notifications: Mapped[List["NotificationMessage"]] = relationship(
        "NotificationMessage", back_populates="created_by_user_role"
    )

    def __repr__(self) -> str:
        return f"<UserRole(id={self.id}, account_id={self.account_id})>"
