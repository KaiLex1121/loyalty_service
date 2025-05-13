from pydantic import BaseModel, Field


class PhoneRequest(BaseModel):
    phone_number: str = Field(..., min_length=10, max_length=15, pattern=r"^\+7[0-9]{10,15}$") # Пример валидации

class OTPVerifyRequest(PhoneRequest):
    otp_code: str = Field(..., min_length=4, max_length=6) # Обычно 4-6 цифр