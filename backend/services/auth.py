import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import (
    create_access_token,
    generate_otp,
    get_otp_expiry_time,
    get_otp_hash,
    verify_otp_hash,
)
from backend.dao.holder import HolderDAO
from backend.enums.back_office import OtpPurposeEnum
from backend.schemas.auth import OTPVerifyRequest
from backend.schemas.otp_code import OtpCodeCreate
from backend.services.account import AccountService
from backend.services.otp_code import OtpCodeService
from backend.services.otp_sending import MockOTPSendingService

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(
        self,
        account_service: AccountService,
        otp_code_service: OtpCodeService,
        otp_sending_service: MockOTPSendingService,
    ):
        self.account_service = account_service
        self.otp_sending_service = otp_sending_service
        self.otp_code_service = otp_code_service

    async def request_otp_for_login(
        self, session: AsyncSession, dao: HolderDAO, phone_number: str
    ) -> None:
        otp_purpose = OtpPurposeEnum.BACKOFFICE_LOGIN
        plain_otp = generate_otp()
        hashed_otp = get_otp_hash(plain_otp)
        otp_expires = get_otp_expiry_time()

        async with session.begin():
            account = await self.account_service.get_or_create_account(
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
                logger.error("Failed to send OTP SMS")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Could not send OTP SMS. Please try again later.",
                )
        print(f"Session {id(session)} in_transaction: {session.in_transaction()}") # Проверяем, есть ли уже активная транзакция
        print(f"Session {id(session)} is_active: {session.is_active}") # Общее состояние сессии

        return account

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
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Account with this phone number not found for OTP verification.",
                )
            active_otp = await dao.otp_code.get_active_otp_by_account_and_purpose(
                session,
                account_id=account.id,
                purpose=otp_data.purpose,
            )
            if not active_otp:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No active OTP found or OTP expired. Please request a new one.",
                )
            if active_otp.is_expired:  # Двойная проверка
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="OTP has expired. Please request a new one.",
                )

            if not verify_otp_hash(
                otp_code=otp_data.otp_code,
                hashed_otp_code=active_otp.hashed_code,
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid OTP code.",
                )
            await self.otp_code_service.set_mark_otp_as_used(
                session, dao, otp_obj=active_otp
            )
            await self.account_service.set_account_as_active(
                account=account
            )
            access_token = create_access_token(subject=account.id)
            return access_token
