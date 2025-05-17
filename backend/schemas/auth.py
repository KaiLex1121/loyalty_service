from pydantic import BaseModel, Field

from backend.core import settings


class PhoneRequest(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")

class OTPVerifyRequest(PhoneRequest):
    otp_code: str = Field(..., min_length=settings.OTP_LENGTH, max_length=settings.OTP_LENGTH)
