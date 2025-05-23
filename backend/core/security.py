import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

from fastapi.security import APIKeyHeader, HTTPBearer, OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import (
    CryptContext,
)  # Пока не используем для OTP, но может пригодиться

from backend.core.settings import settings
from backend.schemas.token import TokenPayload

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token-for-swagger")
# oauth2_scheme = HTTPBearer(auto_error=False)


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta | None = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.SECURITY.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECURITY.SECRET_KEY, algorithm=settings.SECURITY.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenPayload]:
    try:
        payload_dict = jwt.decode(
            token,
            settings.SECURITY.SECRET_KEY,
            algorithms=[settings.SECURITY.ALGORITHM],
        )
        print("asd")
        if "sub" not in payload_dict or "exp" not in payload_dict:
            logger.error("Error decoding token")
            return None

        if not isinstance(payload_dict["exp"], datetime):
            try:
                payload_dict["exp"] = datetime.fromtimestamp(
                    payload_dict["exp"], tz=timezone.utc
                )
            except TypeError:
                logger.error("Error decoding token")
                return None
        token_data = TokenPayload(**payload_dict)

        if token_data.exp and token_data.exp < datetime.now(timezone.utc):
            logger.warning("Token expired")
            return None

        return token_data
    except JWTError:
        logger.error("JWTError", exc_info=True)
        return None
    except Exception:
        logger.error("Error decoding token", exc_info=True)
        return None


def generate_otp(length: int = settings.SECURITY.OTP_LENGTH) -> str:
    return "".join(secrets.choice("0123456789") for _ in range(length))


def get_otp_expiry_time(
    minutes: int = settings.SECURITY.OTP_EXPIRE_MINUTES,
) -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)


def is_otp_valid(otp_expires_at: datetime) -> bool:
    return datetime.utcnow() < otp_expires_at
