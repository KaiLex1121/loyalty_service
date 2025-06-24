import re
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.core.settings import settings
from backend.enums import OtpPurposeEnum


class PhoneNumber(BaseModel):
    """Модель для валидации российских номеров телефонов"""

    phone_number: str = Field(
        ...,
        description="Российский номер телефона",
        examples=[
            "+79991234567",
            "89123456789",
            "79123456789",
            "+7 (912) 345-67-89",
            "8 (912) 345-67-89",
        ],
    )

    @field_validator("phone_number")
    @classmethod
    def validate_russian_phone(cls, v: Any) -> str:
        """
        Валидация российского номера телефона

        Поддерживаемые форматы:
        - +79123456789
        - 89123456789
        - 79123456789
        - +7 (912) 345-67-89
        - 8 (912) 345-67-89
        - 7 (912) 345-67-89
        """
        if not isinstance(v, str):
            raise ValueError("Номер телефона должен быть строкой")

        # Убираем все пробелы, скобки, дефисы
        cleaned = re.sub(r"[\s\(\)\-]", "", v)

        # Проверяем базовый формат
        if not re.match(r"^[\+]?[78]\d{10}$", cleaned):
            raise ValueError(
                "Неверный формат российского номера телефона. "
                "Ожидается формат: +7XXXXXXXXXX, 8XXXXXXXXXX или 7XXXXXXXXXX"
            )

        # Нормализуем номер - приводим к формату +7XXXXXXXXXX
        if cleaned.startswith("+7"):
            normalized = cleaned
        elif cleaned.startswith("8"):
            normalized = "+7" + cleaned[1:]
        elif cleaned.startswith("7"):
            normalized = "+" + cleaned
        else:
            raise ValueError("Номер должен начинаться с +7, 8 или 7")

        # Дополнительная проверка кодов мобильных операторов
        mobile_code = normalized[2:5]  # Берем XXX из +7XXX

        # Основные коды российских мобильных операторов
        valid_mobile_codes = {
            # МТС
            "910",
            "911",
            "912",
            "913",
            "914",
            "915",
            "916",
            "917",
            "918",
            "919",
            "980",
            "981",
            "982",
            "983",
            "984",
            "985",
            "986",
            "987",
            "988",
            "989",
            # Мегафон
            "920",
            "921",
            "922",
            "923",
            "924",
            "925",
            "926",
            "927",
            "928",
            "929",
            "930",
            "931",
            "932",
            "933",
            "934",
            "936",
            "937",
            "938",
            "939",
            # Билайн
            "903",
            "905",
            "906",
            "909",
            "951",
            "952",
            "953",
            "954",
            "955",
            "956",
            "957",
            "958",
            "959",
            # Теле2
            "900",
            "901",
            "902",
            "904",
            "908",
            "950",
            "951",
            "952",
            "953",
            "954",
            "955",
            "956",
            "957",
            "958",
            "959",
            "991",
            "992",
            "993",
            "994",
            "995",
            "996",
            "997",
            "998",
            "999",
            # Йота
            "907",
            # MVNO и другие
            "977",
            "978",
            "900",
            "901",
            "902",
            "903",
            "904",
            "905",
            "906",
            "907",
            "908",
            "909",
            "960",
            "961",
            "962",
            "963",
            "964",
            "965",
            "966",
            "967",
            "968",
            "969",
            "970",
            "971",
            "972",
            "973",
            "974",
            "975",
            "976",
            "977",
            "978",
            "979",
        }

        if mobile_code not in valid_mobile_codes:
            raise ValueError(f"Неизвестный код оператора: {mobile_code}")

        return normalized


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
    )
