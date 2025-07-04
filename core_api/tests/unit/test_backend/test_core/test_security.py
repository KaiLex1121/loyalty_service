import hashlib
import hmac
from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.security import (
    TokenPayload,
    create_access_token,
    generate_otp,
    get_otp_expiry_time,
    get_otp_hash,
    is_otp_valid,
    verify_otp_hash,
    verify_token,
)
from app.core.settings import AppSettings


class TestAccessToken:
    """Тесты для функций работы с JWT токенами"""

    def test_create_access_token_with_custom_expiry(self, test_settings: AppSettings):
        """Тест создания токена с кастомным временем истечения"""
        data = {"sub": "test_user"}
        expires_delta = timedelta(minutes=30)

        token = create_access_token(
            data=data, settings=test_settings, expires_delta=expires_delta
        )

        assert isinstance(token, str)
        assert len(token) > 0

        decoded = jwt.decode(
            token,
            test_settings.SECURITY.JWT_SECRET_KEY,
            algorithms=[test_settings.SECURITY.ALGORITHM],
        )
        assert decoded["sub"] == "test_user"
        assert "exp" in decoded

    def test_create_access_token_with_default_expiry(self, test_settings: AppSettings):
        """Тест создания токена с дефолтным временем истечения"""
        data = {"sub": "test_user"}

        token = create_access_token(data=data, settings=test_settings)

        assert isinstance(token, str)
        decoded = jwt.decode(
            token,
            test_settings.SECURITY.JWT_SECRET_KEY,
            algorithms=[test_settings.SECURITY.ALGORITHM],
        )
        assert decoded["sub"] == "test_user"

        # Более точная проверка времени жизни
        expected_exp = datetime.now(timezone.utc) + timedelta(
            minutes=test_settings.SECURITY.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        assert abs(decoded["exp"] - expected_exp.timestamp()) < 5

    def test_verify_token_valid_token(self, test_settings: AppSettings):
        """Тест верификации валидного токена"""
        data = {"sub": "test_user_valid"}
        token = create_access_token(data=data, settings=test_settings)

        # Верифицируем с помощью реальной функции
        result = verify_token(token=token, settings=test_settings)

        assert result is not None
        assert isinstance(result, TokenPayload)
        assert result.sub == "test_user_valid"

    def test_verify_token_invalid_signature(self, test_settings: AppSettings):
        """Тест верификации токена с неверной подписью"""
        data = {"sub": "test_user_invalid_sig"}
        token = create_access_token(data=data, settings=test_settings)

        # Создаем "плохие" настройки с другим ключом
        bad_settings = test_settings.model_copy()
        bad_settings.SECURITY.JWT_SECRET_KEY = "this-is-a-very-wrong-key"

        result = verify_token(token=token, settings=bad_settings)
        assert result is None

    def test_verify_token_invalid_format(self, test_settings: AppSettings):
        """Тест верификации невалидного формата токена"""
        invalid_token = "invalid.token.here"
        result = verify_token(token=invalid_token, settings=test_settings)
        assert result is None

    def test_verify_token_missing_sub(self, test_settings: AppSettings):
        """Тест верификации токена без поля sub"""
        # Создаем токен вручную, чтобы гарантировать отсутствие sub
        payload = {
            "exp": int((datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp())
        }
        token = jwt.encode(
            payload,
            test_settings.SECURITY.JWT_SECRET_KEY,
            algorithm=test_settings.SECURITY.ALGORITHM,
        )
        result = verify_token(token=token, settings=test_settings)
        assert result is None

    def test_verify_token_missing_exp(self, test_settings: AppSettings):
        """Тест верификации токена без поля exp"""
        payload = {"sub": "test_user_no_exp"}
        token = jwt.encode(
            payload,
            test_settings.SECURITY.JWT_SECRET_KEY,
            algorithm=test_settings.SECURITY.ALGORITHM,
        )

        result = verify_token(token=token, settings=test_settings)
        assert result is None

    def test_verify_token_expired(self, test_settings: AppSettings):
        """Тест верификации истекшего токена"""
        data = {"sub": "expired_user"}
        # Создаем токен, который уже истек
        expired_delta = timedelta(minutes=-5)
        token = create_access_token(
            data=data, settings=test_settings, expires_delta=expired_delta
        )

        result = verify_token(token=token, settings=test_settings)
        assert result is None


# --- Тесты для OTP ---


class TestOTP:
    """Тесты для функций работы с OTP"""

    def test_generate_otp_default_length(self, test_settings: AppSettings):
        """Тест генерации OTP с дефолтной длиной из настроек"""
        otp = generate_otp(settings=test_settings)

        assert isinstance(otp, str)
        assert len(otp) == test_settings.SECURITY.OTP_LENGTH
        assert otp.isdigit()

    def test_generate_otp_different_each_time(self, test_settings: AppSettings):
        """Тест что генерируются разные OTP коды"""
        # Используем set для проверки уникальности
        otps = {generate_otp(settings=test_settings) for _ in range(10)}
        assert len(otps) > 1  # Крайне маловероятно, что будет 1

    def test_get_otp_hash(self, test_settings: AppSettings):
        """Тест получения хеша OTP"""
        otp = "123456"
        otp_hash = get_otp_hash(otp=otp, settings=test_settings)

        assert isinstance(otp_hash, str)
        assert len(otp_hash) == 64  # SHA256 hex digest

        expected_hash = hmac.new(
            test_settings.SECURITY.HMAC_SECRET_KEY.encode("utf-8"),
            otp.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        assert otp_hash == expected_hash

    def test_verify_otp_hash_valid(self, test_settings: AppSettings):
        """Тест верификации валидного OTP хеша"""
        otp = "123456"
        otp_hash = get_otp_hash(otp=otp, settings=test_settings)

        result = verify_otp_hash(
            otp_code=otp, hashed_otp_code=otp_hash, settings=test_settings
        )
        assert result is True

    def test_verify_otp_hash_invalid(self, test_settings: AppSettings):
        """Тест верификации невалидного OTP хеша"""
        otp = "123456"
        wrong_otp = "654321"
        otp_hash = get_otp_hash(otp=otp, settings=test_settings)

        result = verify_otp_hash(
            otp_code=wrong_otp, hashed_otp_code=otp_hash, settings=test_settings
        )
        assert result is False

    def test_get_otp_expiry_time_default(self, test_settings: AppSettings):
        """Тест получения времени истечения OTP с дефолтными настройками"""
        before_call = datetime.now(timezone.utc)
        expiry_time = get_otp_expiry_time(settings=test_settings)
        after_call = datetime.now(timezone.utc)

        expected_min = before_call + timedelta(
            minutes=test_settings.SECURITY.OTP_EXPIRE_MINUTES
        )
        expected_max = after_call + timedelta(
            minutes=test_settings.SECURITY.OTP_EXPIRE_MINUTES
        )

        assert expected_min <= expiry_time <= expected_max

    def test_is_otp_valid(self):
        """Тесты для функции is_otp_valid, которая не зависит от settings"""
        assert is_otp_valid(datetime.now(timezone.utc) + timedelta(seconds=1)) is True
        assert is_otp_valid(datetime.now(timezone.utc) - timedelta(seconds=1)) is False
        assert is_otp_valid(datetime.now(timezone.utc)) is False
