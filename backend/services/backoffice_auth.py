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
from backend.enums import OtpPurposeEnum
from backend.enums.auth_enums import UserAccessLevelEnum
from backend.exceptions import (
    AccountNotFoundException,
    InvalidOTPException,
    OTPExpiredException,
    OTPNotFoundException,
    OTPSendingException,
)
from backend.schemas.account import AccountInDBBase, AccountResponse, AccountUpdate
from backend.schemas.backoffice_auth import OTPVerifyRequest
from backend.schemas.otp_code import OtpCodeCreate
from backend.schemas.token import TokenResponse
from backend.services.account import AccountService
from backend.services.otp_code import (
    OtpCodeService,
)
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

        account = await self.account_service.get_account_by_phone(
            session, dao, phone_number=phone_number
        )
        if not account:
            # Создаем аккаунт, если не найден. Ошибки создания обработаются в AccountService
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
            raise OTPSendingException(
                internal_details={"phone_number": account.phone_number}
            )
        return AccountResponse.model_validate(account)

    async def verify_otp_and_login(
        self,
        session: AsyncSession,
        dao: HolderDAO,
        otp_data: OTPVerifyRequest,
    ) -> TokenResponse:
        account = await self.account_service.get_account_by_phone(
            session, dao, phone_number=otp_data.phone_number
        )
        if not account:
            raise AccountNotFoundException(
                identifier=otp_data.phone_number,
                identifier_type="phone number",
                internal_details={"purpose": otp_data.purpose.value},
            )

        active_otp = await dao.otp_code.get_active_otp_by_account_and_purpose(
            session,
            account_id=account.id,
            purpose=otp_data.purpose,
        )
        if not active_otp:
            raise OTPNotFoundException(
                internal_details={
                    "account_id": account.id,
                    "purpose": otp_data.purpose.value,
                }
            )

        if active_otp.is_expired:
            raise OTPExpiredException(
                internal_details={
                    "account_id": account.id,
                    "otp_id": active_otp.id,
                    "expires_at": active_otp.expires_at.isoformat(),
                }
            )

        if not verify_otp_hash(
            otp_code=otp_data.otp_code,
            hashed_otp_code=active_otp.hashed_code,
            settings=self.settings,
        ):
            raise InvalidOTPException(
                internal_details={"account_id": account.id, "otp_id": active_otp.id}
            )

        await self.otp_code_service.set_mark_otp_as_used(
            session, dao, otp_obj=active_otp
        )

        await self.account_service.update_account(
            session=session,
            dao=dao,
            account_db=account,
            account_in=AccountUpdate(is_active=True),
        )

        jwt_scopes = ["backoffice_user"]
        if (
            account.user_profile
            and account.user_profile.access_level == UserAccessLevelEnum.FULL_ADMIN
        ):
            jwt_scopes.append("backoffice_admin")
        print("jwt_scopes", jwt_scopes)
        access_token = create_access_token(
            data={"sub": str(account.id)}, settings=self.settings, scopes=jwt_scopes
        )

        return TokenResponse(access_token=access_token, token_type="bearer")
