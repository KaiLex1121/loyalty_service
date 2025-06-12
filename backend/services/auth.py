from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.logger import get_logger
from backend.core.security import (
    create_access_token,
    generate_otp,
    get_otp_expiry_time,
    get_otp_hash,
    verify_otp_hash,
)
from backend.core.settings import AppSettings
from backend.dao.holder import HolderDAO
from backend.enums.back_office import OtpPurposeEnum
from backend.exceptions.account import AccountNotFoundException
from backend.exceptions.auth import (
    InvalidOTPException,
    OTPExpiredException,
    OTPNotFoundException,
    OTPSendingException,
)
from backend.schemas.account import AccountInDBBase
from backend.schemas.auth import OTPVerifyRequest
from backend.schemas.otp_code import OtpCodeCreate
from backend.services.account import AccountService
from backend.services.otp_code import OtpCodeService
from backend.services.otp_sending import MockOTPSendingService

logger = get_logger(__name__)


class AuthService:
    def __init__(
        self,
        account_service: AccountService,
        otp_code_service: OtpCodeService,
        otp_sending_service: MockOTPSendingService,
        settings: AppSettings,
    ):
        self.account_service = account_service
        self.otp_sending_service = otp_sending_service
        self.otp_code_service = otp_code_service
        self.settings = settings

    async def request_otp_for_login(
        self, session: AsyncSession, dao: HolderDAO, phone_number: str
    ) -> AccountInDBBase:
        otp_purpose = OtpPurposeEnum.BACKOFFICE_LOGIN
        plain_otp = generate_otp(self.settings)
        hashed_otp = get_otp_hash(plain_otp, self.settings)
        otp_expires = get_otp_expiry_time(self.settings)

        async with session.begin():
            account = await self.account_service.get_account_by_phone(
                session, dao, phone_number=phone_number
            )
            if not account:
                account = await self.account_service.create_account_by_phone(
                    session, dao, phone_number=phone_number
                )

            await self.otp_code_service.invalidate_previous_otps(
                session, dao, account=account, purpose=otp_purpose
            )

            otp_code_schema = OtpCodeCreate(
                hashed_code=hashed_otp,
                expires_at=otp_expires,
                purpose=otp_purpose,
                account_id=account.id,
                channel="tg_userbot",
            )
            await self.otp_code_service.create_otp(
                dao=dao,
                session=session,
                obj_in=otp_code_schema,
            )

            sms_sent = await self.otp_sending_service.send_otp(
                phone_number=account.phone_number, otp_code=plain_otp
            )
            if not sms_sent:
                logger.error(f"Failed to send OTP SMS to {account.phone_number}")
                raise OTPSendingException(phone_number=account.phone_number)

        return AccountInDBBase.model_validate(account)

    async def verify_otp_and_login(
        self,
        session: AsyncSession,
        dao: HolderDAO,
        otp_data: OTPVerifyRequest,
    ) -> str:
        async with session.begin():
            account = await self.account_service.get_account_by_phone(
                session, dao, phone_number=otp_data.phone_number
            )
            if not account:
                raise AccountNotFoundException(phone_number=otp_data.phone_number)

            active_otp = await dao.otp_code.get_active_otp_by_account_and_purpose(
                session,
                account_id=account.id,
                purpose=otp_data.purpose,
            )
            if not active_otp:
                raise OTPNotFoundException()

            if active_otp.is_expired:
                raise OTPExpiredException()

            if not verify_otp_hash(
                otp_code=otp_data.otp_code,
                hashed_otp_code=active_otp.hashed_code,
                settings=self.settings,
            ):
                raise InvalidOTPException()

            await self.otp_code_service.set_mark_otp_as_used(
                session, dao, otp_obj=active_otp
            )
            await self.account_service.set_account_as_active(account=account)

            access_token = create_access_token(
                data={"sub": str(account.id)}, settings=self.settings
            )
            return access_token
