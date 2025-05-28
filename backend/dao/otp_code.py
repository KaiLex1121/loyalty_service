from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.base import BaseDAO
from backend.enums.back_office import OtpPurposeEnum
from backend.models.otp_code import OtpCode


class OtpCodeDAO(BaseDAO[OtpCode]):
    def __init__(self):
        super().__init__(OtpCode)

    async def create_otp(
        self,
        session: AsyncSession,
        *,
        hashed_otp: str,
        expires_at: datetime,
        purpose: str,
        account_id: int,
        channel: str,
    ) -> OtpCode:
        db_obj = self.model(
            hashed_code=hashed_otp,
            expires_at=expires_at,
            purpose=purpose,
            account_id=account_id,
            channel=channel,
        )
        session.add(db_obj)

    async def get_active_otp_by_account_and_purpose(
        self,
        session: AsyncSession,
        *,
        account_id: int,
        purpose: OtpPurposeEnum,
    ) -> OtpCode | None:
        stmt = (
            select(self.model)
            .where(self.model.account_id == account_id)
            .where(self.model.purpose == purpose)
            .where(self.model.is_used == False)
            .where(self.model.expires_at > datetime.now(timezone.utc))
            .order_by(self.model.created_at.desc())
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_otp_as_used(
        self, session: AsyncSession, *, otp_obj: OtpCode
    ) -> OtpCode:
        otp_obj.is_used = True
        session.add(otp_obj)
        return otp_obj

    async def invalidate_previous_otps(
        self, session: AsyncSession, *, account_id: int, purpose: OtpPurposeEnum
    ) -> None:
        stmt = (
            update(self.model)
            .where(self.model.account_id == account_id)
            .where(self.model.purpose == purpose)
            .where(self.model.is_used == False)
            .values(is_used=True, updated_at=datetime.now(timezone.utc))
        )
        await session.execute(stmt)
