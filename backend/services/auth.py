import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import (create_access_token, generate_otp,
                                   get_otp_expiry_time, get_otp_hmac_hash)
from backend.dao.holder import HolderDAO
from backend.models.account import Account
from backend.services.account import AccountService
from backend.services.otp_code import OtpCodeService
from backend.services.otp_sending import MockOTPSendingService
from common.enums.back_office import OtpPurposeEnum

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

    async def request_otp(
        self, db: AsyncSession, dao: HolderDAO, phone_number: str
    ) -> None:
        otp_purpose = OtpPurposeEnum.BACKOFFICE_LOGIN
        account = await self.account_service.get_or_create_account_for_otp(
            db, dao, phone_number=phone_number
        )

        await self.otp_code_service.invalidate_previous_otps(
            db, dao, account=account, purpose=otp_purpose
        )

        plain_otp = generate_otp()
        hashed_otp = get_otp_hmac_hash(plain_otp)
        otp_expires = get_otp_expiry_time()

        await dao.otp_code.create_otp(
            db,
            account_id=account.id,
            purpose=otp_purpose,
            hashed_otp=hashed_otp,
            expires_at=otp_expires,
        )

        sms_sent = await self.otp_sending_service.send_otp(
            phone_number=account.phone_number, otp_code=plain_otp
        )
        if not sms_sent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not send OTP SMS. Please try again later.",
            )

    async def verify_otp_and_login(
        self, db: AsyncSession, dao: HolderDAO, phone_number: str, otp_code: str
    ) -> str:
        account = await self.account_service.get_account_by_phone(
            db, dao, phone_number=phone_number
        )
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="account with this phone number not found for OTP verification.",
            )

        if not account.otp_code or account.otp_code != otp_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP code."
            )

        if not account.otp_expires_at or account.otp_expires_at < datetime.now(
            timezone.utc
        ):
            await self.account_service.activate_account_and_clear_otp(
                db, dao, account=account
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP code has expired. Please request a new one.",
            )

        account = await self.account_service.activate_account_and_clear_otp(
            db, dao, account=account
        )

        access_token = create_access_token(subject=account.phone_number)
        return access_token
