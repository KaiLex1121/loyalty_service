from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.holder import HolderDAO
from backend.models.account import Account
from backend.models.otp_code import OtpCode
from backend.schemas.otp_code import OtpCodeCreate


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
        self, session: AsyncSession, dao: HolderDAO, obj_in: OtpCodeCreate
    ):
        if obj_in is None:
            raise TypeError("Expected OtpCodeCreate object, got None instead")
        otp_code = await dao.otp_code.create(session, obj_in=obj_in)
        return otp_code

    async def set_mark_otp_as_used(
        self, session: AsyncSession, dao: HolderDAO, otp_obj: OtpCode
    ) -> None:
        if otp_obj is None:
            raise TypeError("Expected OtpCode object, got None instead")
        await dao.otp_code.mark_otp_as_used(session, otp_obj=otp_obj)
