# --- Схемы для поиска клиента сотрудником ---
import decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.utils.validators import OTPCode, RussianPhoneNumber


class CustomerSearchByPhoneRequest(BaseModel):
    customer_phone_number: RussianPhoneNumber


class AccrueCashbackRequest(CustomerSearchByPhoneRequest):
    purchase_amount: decimal.Decimal = Field(
        ..., gt=0, description="Общая сумма покупки клиента. Должна быть больше нуля."
    )
    outlet_id: Optional[int] = Field(
        None, description="ID торговой точки, где совершена покупка."
    )

    @field_validator("outlet_id")
    @classmethod
    def validate_outlet_id(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError(
                "ID торговой точки (outlet_id) должен быть положительным числом."
            )
        return v


class SpendCashbackRequestOTP(CustomerSearchByPhoneRequest):
    """Запрос на начало списания и отправку OTP."""

    purchase_amount: decimal.Decimal = Field(
        ...,
        gt=0,
        description="Общая сумма покупки клиента, в счет которой списывается кэшбэк.",
    )
    outlet_id: Optional[int] = Field(None, description="ID торговой точки.")

    @field_validator("outlet_id")
    @classmethod
    def validate_outlet_id(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError(
                "ID торговой точки (outlet_id) должен быть положительным числом."
            )
        return v


class SpendCashbackVerifyOTP(CustomerSearchByPhoneRequest):
    """Подтверждение списания с помощью OTP."""

    otp_code: OTPCode
    purchase_amount: decimal.Decimal = Field(
        ...,
        gt=0,
        description="Общая сумма покупки (должна совпадать с суммой из запроса OTP).",
    )
    outlet_id: Optional[int] = Field(
        None, description="ID торговой точки (должен совпадать с ID из запроса OTP)."
    )


class SpendCashbackRequestOTPResponse(BaseModel):
    """Ответ на запрос OTP для списания."""

    message: str = "Код подтверждения отправлен клиенту."
    amount_to_spend: decimal.Decimal = Field(
        description="Сумма кэшбэка, которая будет списана после подтверждения."
    )
    customer_phone_masked: str = Field(
        description="Маскированный номер телефона клиента, на который отправлен код."
    )


class SpendCashbackVerifyRequest(BaseModel):
    """Запрос на подтверждение списания с OTP кодом."""

    otp_code: OTPCode
