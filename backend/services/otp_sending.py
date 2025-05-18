import logging
import random

logger = logging.getLogger(__name__)


class MockOTPSendingService:

    @staticmethod
    async def send_otp(phone_number: str, otp_code: str) -> bool:
        logger.info(f"MOCK SMS to {phone_number}: {otp_code}")
        return True
