from app.core.logger import get_logger

logger = get_logger(__name__)


class MockOTPSendingService:

    @staticmethod
    async def send_otp(phone_number: str, otp_code: str) -> bool:
        logger.info(f"MOCK SMS to {phone_number}: {otp_code}")
        return True
