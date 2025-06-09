import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from backend.core.settings import AppSettings
from backend.schemas.token import TokenPayload

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token-for-swagger")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(
    data: dict, settings: AppSettings, expires_delta: timedelta | None = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.SECURITY.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = data.copy()
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECURITY.JWT_SECRET_KEY,
        algorithm=settings.SECURITY.ALGORITHM,
    )
    return encoded_jwt


def verify_token(token: str, settings: AppSettings) -> Optional[TokenPayload]:
    """
    Верифицирует JWT токен.

    Проверяет подпись, срок годности и структуру полезной нагрузки.
    Возвращает объект TokenPayload в случае успеха или None в случае любой ошибки.
    """
    try:
        payload_dict = jwt.decode(
            token,
            settings.SECURITY.JWT_SECRET_KEY,
            algorithms=[settings.SECURITY.ALGORITHM],
        )
        token_data = TokenPayload(**payload_dict)
        return token_data

    except jwt.ExpiredSignatureError:
        logger.info("Token has expired.")
        return None
    except jwt.JWTError as e:
        logger.error(f"JWT decoding error: {e}")
        return None
    except ValidationError as e:
        logger.error(f"Invalid token payload structure: {e}")
        return None


def generate_otp(settings: AppSettings) -> str:
    length = settings.SECURITY.OTP_LENGTH
    return "".join(secrets.choice("0123456789") for _ in range(length))
    # return "123456"


def get_otp_hash(otp: str, settings: AppSettings) -> str:
    key = settings.SECURITY.HMAC_SECRET_KEY.encode("utf-8")
    msg = otp.encode("utf-8")
    hmac_hash = hmac.new(key, msg, hashlib.sha256).hexdigest()
    return hmac_hash


def verify_otp_hash(otp_code: str, hashed_otp_code: str, settings: AppSettings) -> bool:
    return get_otp_hash(otp_code, settings) == hashed_otp_code


def get_otp_expiry_time(
    settings: AppSettings,
) -> datetime:
    minutes = settings.SECURITY.OTP_EXPIRE_MINUTES
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)


def is_otp_valid(otp_expires_at: datetime) -> bool:
    return datetime.now(timezone.utc) < otp_expires_at
