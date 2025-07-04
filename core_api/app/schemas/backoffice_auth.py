import re
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.enums import OtpPurposeEnum
from app.utils.validators import OTPCode, RussianPhoneNumber


class PhoneNumberRequest(BaseModel):
    phone_number: RussianPhoneNumber


class OTPVerifyRequest(BaseModel):
    phone_number: RussianPhoneNumber
    otp_code: OTPCode
    purpose: OtpPurposeEnum = Field(
        default=OtpPurposeEnum.BACKOFFICE_LOGIN,
        examples=[OtpPurposeEnum.BACKOFFICE_LOGIN],
    )
