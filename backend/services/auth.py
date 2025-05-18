import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import (create_access_token, generate_otp,
                                   get_otp_expiry_time)
from backend.dao.holder import HolderDAO
from backend.models.user import User
from backend.services.otp_sending import MockOTPSendingService
from backend.services.user import UserService

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(
        self, user_service: UserService, otp_sending_service: MockOTPSendingService
    ):
        self.user_service = user_service
        self.otp_sending_service = otp_sending_service

    async def request_otp(
        self, db: AsyncSession, dao: HolderDAO, phone_number: str
    ) -> User:
        user = await self.user_service.get_or_create_user_for_otp(
            db, dao, phone_number=phone_number
        )

        otp = generate_otp()
        otp_expires = get_otp_expiry_time()

        user = await self.user_service.set_otp_for_user(
            db, dao, user=user, otp_code=otp, otp_expires_at=otp_expires
        )

        sms_sent = await self.otp_sending_service.send_otp(
            phone_number=user.phone_number, otp_code=otp
        )
        if not sms_sent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not send OTP SMS. Please try again later.",
            )
        return user

    async def verify_otp_and_login(
        self, db: AsyncSession, dao: HolderDAO, phone_number: str, otp_code: str
    ) -> str:
        user = await self.user_service.get_user_by_phone(
            db, dao, phone_number=phone_number
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User with this phone number not found for OTP verification.",
            )

        if not user.otp_code or user.otp_code != otp_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP code."
            )

        if not user.otp_expires_at or user.otp_expires_at < datetime.now(timezone.utc):
            await self.user_service.activate_user_and_clear_otp(db, dao, user=user)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP code has expired. Please request a new one.",
            )

        user = await self.user_service.activate_user_and_clear_otp(db, dao, user=user)

        access_token = create_access_token(subject=user.phone_number)
        return access_token
