import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional

from app.core.logger import get_logger
from app.core.settings import AppSettings
from app.schemas.token import TokenPayload
from fastapi.security import APIKeyHeader, HTTPBearer, OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError

logger = get_logger(__name__)

internal_api_key_header = APIKeyHeader(
    name="X-Internal-API-Key", auto_error=False, scheme_name="InternalAPIKeyAuth"
)

http_bearer_backoffice = HTTPBearer(
    scheme_name="BackofficeUserHttpAuth",
    description="JWT токен для доступа к бэк-офису",
    auto_error=True,
)

http_bearer_employee = HTTPBearer(
    scheme_name="EmployeeHttpAuth",
    description="JWT токен для доступа к бэк-офису",
    auto_error=True,
)

oauth2_scheme_backoffice = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token-for-swagger",
    description="Аутентификация для пользователей бэк-офиса. Введите 'Bearer <token>'.",
    scheme_name="BackofficeBearerAuth",
    scopes={
        "backoffice_user": "Доступ к ресурсам бэк-офиса компании.",
        "backoffice_admin": "Полный доступ системного администратора.",
    },
    auto_error=True,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(
    data: dict[str, Any],
    settings: AppSettings,
    expires_delta: Optional[timedelta] = None,
    scopes: Optional[List[str]] = None,
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.SECURITY.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode["scopes"] = scopes if scopes else []
    to_encode["exp"] = expire

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECURITY.JWT_SECRET_KEY,
        algorithm=settings.SECURITY.ALGORITHM,
    )
    return encoded_jwt

def generate_otp(settings: AppSettings) -> str:
    settings.SECURITY.OTP_LENGTH
    # return "".join(secrets.choice("0123456789") for _ in range(length))
    return "123456"


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
