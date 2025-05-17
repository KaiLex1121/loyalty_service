from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user import User
from backend.core.security import generate_otp_code, get_otp_expiry_time, create_access_token
from backend.services.otp_sending import MockOTPSendingService
from backend.services.user import UserService
import logging


logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, user_service: UserService, otp_sending_service: MockOTPSendingService):
        self.user_service = user_service
        self.otp_sending_service = otp_sending_service


    async def request_otp(self, db: AsyncSession, phone_number: str) -> User:
        user = await self.user_service.get_or_create_user_for_otp(db, phone_number=phone_number)

        otp = generate_otp_code()
        otp_expires = get_otp_expiry_time()

        user = await self.user_service.set_otp_for_user(db, user=user, otp_code=otp, otp_expires_at=otp_expires)

        sms_sent = await self.otp_sending_service.send_otp(phone_number=user.phone_number, otp_code=otp)
        if not sms_sent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not send OTP SMS. Please try again later."
            )
        return user

    async def verify_otp_and_login(self, db: AsyncSession, phone_number: str, otp_code: str) -> str:
        user = await self.user_service.get_user_by_phone(db, phone_number=phone_number)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User with this phone number not found for OTP verification."
            )

        if not user.otp_code or user.otp_code != otp_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP code."
            )

        if not user.otp_expires_at or user.otp_expires_at < datetime.now(timezone.utc):
            await self.user_service.activate_user_and_clear_otp(db, user=user)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP code has expired. Please request a new one."
            )

        user = await self.user_service.activate_user_and_clear_otp(db, user=user)

        access_token = create_access_token(subject=user.phone_number)
        return access_token
