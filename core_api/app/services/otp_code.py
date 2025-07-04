from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.holder import HolderDAO
from app.enums import OtpPurposeEnum
from app.models.account import Account
from app.models.otp_code import OtpCode
from app.schemas.otp_code import OtpCodeCreate


class OtpCodeService:

    async def invalidate_previous_otps(
        self,
        session: AsyncSession,
        dao: HolderDAO,
        account: Account,
        purpose: OtpPurposeEnum,
    ) -> None:
        await dao.otp_code.invalidate_previous_otps(
            session,
            account_id=account.id,
            purpose=purpose,
        )

    async def create_otp(
        self, session: AsyncSession, dao: HolderDAO, obj_in: OtpCodeCreate
    ):
        otp_code = await dao.otp_code.create(session, obj_in=obj_in)
        return otp_code

    async def set_mark_otp_as_used(
        self, session: AsyncSession, dao: HolderDAO, otp_obj: OtpCode
    ) -> None:
        await dao.otp_code.mark_otp_as_used(session, otp_obj=otp_obj)
