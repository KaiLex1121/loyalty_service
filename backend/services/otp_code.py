from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.holder import HolderDAO
from backend.models.account import Account
from backend.models.otp_code import OtpCode
from common.enums.back_office import OtpPurposeEnum


class OtpCodeService:

    async def invalidate_previous_otps(
        self, session: AsyncSession, dao: HolderDAO, account: Account, purpose: str
    ) -> None:
        await dao.otp_code.invalidate_previous_otps(
            session,
            account_id=account.id,
            purpose=purpose,
        )

    async def create_otp(
        self,
        session: AsyncSession,
        dao: HolderDAO,
        *,
        hashed_otp: str,
        expires_at: datetime,
        purpose: str,
        account_id: int,
        channel: str,
    ):
        otp_code = await dao.otp_code.create_otp(
            session=session,
            hashed_otp=hashed_otp,
            expires_at=expires_at,
            purpose=purpose,
            account_id=account_id,
            channel=channel,
        )
        return otp_code

    async def set_mark_otp_as_used(
        self, session: AsyncSession, dao: HolderDAO, otp_obj: OtpCode
    ) -> None:
        await dao.otp_code.mark_otp_as_used(session, otp_obj=otp_obj)
