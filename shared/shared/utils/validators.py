import re
from typing import Annotated, Any

from pydantic import AfterValidator, Field


def validate_russian_phone(phone: Any) -> str:
    """
    Валидация российского номера телефона с проверкой кодов операторов.
    Приводит номер к формату +7XXXXXXXXXX.
    """
    if not isinstance(phone, str):
        raise ValueError("Номер телефона должен быть строкой.")

    # Убираем все пробелы, скобки, дефисы
    cleaned = re.sub(r"[\s\(\)\-]", "", phone)

    # Проверяем базовый формат
    if not re.match(r"^[\+]?[78]\d{10}$", cleaned):
        raise ValueError(
            "Неверный формат номера. Ожидается 11 цифр, например, +79123456789 или 89123456789."
        )

    # Нормализуем номер - приводим к формату +7XXXXXXXXXX
    if cleaned.startswith("+7"):
        normalized = cleaned
    elif cleaned.startswith("8"):
        normalized = "+7" + cleaned[1:]
    elif cleaned.startswith("7"):
        normalized = "+" + cleaned
    else:
        # Эта ветка почти недостижима из-за regex выше, но для надежности оставим
        raise ValueError("Номер должен начинаться с +7, 8 или 7.")

    # Дополнительная проверка кодов мобильных операторов
    mobile_code = normalized[2:5]

    valid_mobile_codes = {
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
        "900",
        "901",
        "902",
        "904",
        "908",
        "950",
        "991",
        "992",
        "993",
        "994",
        "995",
        "996",
        "997",
        "998",
        "999",
        "907",
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
        raise ValueError(f"Неизвестный или неверный код оператора: {mobile_code}.")

    return normalized


def validate_otp_code(otp: Any) -> str:
    """
    Валидация OTP кода.

    Args:
        otp: OTP код для валидации

    Returns:
        Валидный OTP код как строка

    Raises:
        ValueError: Если OTP код имеет неверный формат
    """
    if not isinstance(otp, (str, int)):
        raise ValueError("OTP код должен быть строкой или числом")

    # Приводим к строке
    otp_str = str(otp).strip()

    # Проверяем длину
    if len(otp_str) != 6:
        raise ValueError("OTP код должен содержать 6 символов")

    # Проверяем, что содержит только цифры
    if not otp_str.isdigit():
        raise ValueError("OTP код должен содержать только цифры")

    return otp_str


OTPCode = Annotated[
    str,
    AfterValidator(validate_otp_code),
    Field(
        description="Полученный OTP код",
        examples=["123456"],
        min_length=6,
        max_length=6,
    ),
]


# Создаем аннотированный тип для переиспользования в схемах
RussianPhoneNumber = Annotated[
    str,
    AfterValidator(validate_russian_phone),
    Field(
        description="Российский номер телефона с проверкой кода оператора",
        examples=[
            "+79991234567",
            "89123456789",
            "79123456789",
            "+7 (912) 345-67-89",
            "8 (912) 345-67-89",
        ],
        min_length=10,
        max_length=18,  # Учитываем пробелы и символы в примерах
    ),
]
