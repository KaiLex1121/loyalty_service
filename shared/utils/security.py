import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt, ExpiredSignatureError
from pydantic import ValidationError

from shared.schemas.schemas import TokenPayload

# --- JWT Token Verification ---

def verify_token(
    token: str,
    secret_key: str,
    algorithm: str,
) -> Optional[TokenPayload]:
    """
    Верифицирует JWT токен. Эта функция является чистой и не зависит
    от конфигурационных объектов конкретных сервисов.
    """
    if not token:
        return None
    try:
        payload_dict = jwt.decode(token, secret_key, algorithms=[algorithm])
        token_data = TokenPayload(**payload_dict)
        return token_data
    except ExpiredSignatureError:
        return None
    except (JWTError, ValidationError):
        return None

# --- OTP (One-Time Password) Utilities ---

def generate_otp(length: int = 6) -> str:
    """
    Генерирует криптографически безопасный OTP-код заданной длины.
    Не зависит от настроек.
    """
    if length < 4 or length > 8:
        raise ValueError("OTP length must be between 4 and 8 digits.")
    return "".join(secrets.choice("0123456789") for _ in range(length))

def get_otp_hash(otp: str, hmac_secret_key: str) -> str:
    """
    Создает HMAC-SHA256 хэш для OTP-кода.
    Не зависит от настроек.
    """
    key = hmac_secret_key.encode("utf-8")
    msg = otp.encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()

def verify_otp_hash(otp_code: str, hashed_otp_code: str, hmac_secret_key: str) -> bool:
    """
    Проверяет, соответствует ли OTP-код предоставленному хэшу.
    Не зависит от настроек.
    """
    return get_otp_hash(otp_code, hmac_secret_key) == hashed_otp_code

def get_otp_expiry_time(expire_minutes: int) -> datetime:
    """
    Возвращает время истечения срока действия OTP.
    Не зависит от настроек.
    """
    return datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)

def is_otp_valid(otp_expires_at: datetime) -> bool:
    """
    Проверяет, не истек ли срок действия OTP.
    """
    return datetime.now(timezone.utc) < otp_expires_at