import re

from pydantic import BaseModel, Field, model_validator

from backend.core.settings import settings
from backend.enums.back_office import OtpPurposeEnum


class PhoneNumber(BaseModel):
    phone_number: str = Field(
        ...,
        description="Российский номер телефона в формате +7XXXXXXXXXX или 8XXXXXXXXXX",
        examples=["+79991234567"],
    )

    @model_validator(mode="after")
    def validate_phone_number(self) -> "PhoneNumber":
        pattern = (
            r"^(?:\+7|8)[\s\-]?\(?(\d{3})\)?[\s\-]?(\d{3})[\s\-]?(\d{2})[\s\-]?(\d{2})$"
        )
        phone = self.phone_number.strip()
        if not re.match(pattern, phone):
            raise ValueError(
                "Некорректный формат российского номера телефона. "
                "Должен начинаться с +7 или 8 и содержать 10 цифр после кода страны. "
                "Например: +79991234567 или 89991234567"
            )

        digits_only = re.sub(r"\D", "", phone)
        if digits_only.startswith("8"):
            digits_only = "7" + digits_only[1:]
        if not digits_only.startswith("7"):
            digits_only = "7" + digits_only
        self.phone_number = "+" + digits_only

        return self


class PhoneNumberRequest(PhoneNumber):
    pass


class OTPVerifyRequest(PhoneNumber):
    otp_code: str = Field(
        ...,
        min_length=settings.SECURITY.OTP_LENGTH,
        max_length=settings.SECURITY.OTP_LENGTH,
    )
    purpose: OtpPurposeEnum = Field(
        default=OtpPurposeEnum.BACKOFFICE_LOGIN,
        examples=[OtpPurposeEnum.BACKOFFICE_LOGIN],
    )  # Или OtpPurposeEnum.BACKOFFICE_LOGIN
