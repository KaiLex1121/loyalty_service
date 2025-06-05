import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from jose import jwt

from backend.core.security import (create_access_token, generate_otp,
                                   get_otp_expiry_time, get_otp_hash,
                                   get_password_hash, is_otp_valid,
                                   verify_otp_hash, verify_token)


class TestPasswordHashing:
    """Тесты для функций работы с паролями"""

    def test_get_password_hash_returns_string(self):
        """Тест что get_password_hash возвращает строку"""
        password = "test_password"
        hashed = get_password_hash(password)

        assert isinstance(hashed, str)
        assert hashed != password
        assert len(hashed) > 0

    def test_get_password_hash_different_passwords_different_hashes(self):
        """Тест что разные пароли дают разные хеши"""
        password1 = "password1"
        password2 = "password2"

        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)

        assert hash1 != hash2

    def test_get_password_hash_same_password_different_hashes(self):
        """Тест что один пароль дает разные хеши (из-за salt)"""
        password = "test_password"

        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2


class TestAccessToken:
    """Тесты для функций работы с JWT токенами"""

    @patch("backend.core.security.settings")
    def test_create_access_token_with_custom_expiry(self, mock_settings):
        """Тест создания токена с кастомным временем истечения"""
        mock_settings.SECURITY.JWT_SECRET_KEY = "test_secret_key"
        mock_settings.SECURITY.ALGORITHM = "HS256"

        data = {"sub": "test_user"}
        expires_delta = timedelta(minutes=30)

        token = create_access_token(data, expires_delta)

        assert isinstance(token, str)
        assert len(token) > 0

        # Декодируем токен для проверки содержимого
        decoded = jwt.decode(token, "test_secret_key", algorithms=["HS256"])
        assert decoded["sub"] == "test_user"
        assert "exp" in decoded

    @patch("backend.core.security.settings")
    def test_create_access_token_with_default_expiry(self, mock_settings):
        """Тест создания токена с дефолтным временем истечения"""
        mock_settings.SECURITY.JWT_SECRET_KEY = "test_secret_key"
        mock_settings.SECURITY.ALGORITHM = "HS256"
        mock_settings.SECURITY.ACCESS_TOKEN_EXPIRE_MINUTES = 60

        data = {"sub": "test_user"}

        token = create_access_token(data)

        assert isinstance(token, str)
        decoded = jwt.decode(token, "test_secret_key", algorithms=["HS256"])
        assert decoded["sub"] == "test_user"

    @patch("backend.core.security.settings")
    @patch("backend.core.security.TokenPayload")
    def test_verify_token_valid_token(self, mock_token_payload, mock_settings):
        """Тест верификации валидного токена"""
        mock_settings.SECURITY.JWT_SECRET_KEY = "test_secret_key"
        mock_settings.SECURITY.ALGORITHM = "HS256"

        # Создаем валидный токен
        future_time = datetime.now(timezone.utc) + timedelta(minutes=30)
        payload = {"sub": "test_user", "exp": int(future_time.timestamp())}
        token = jwt.encode(payload, "test_secret_key", algorithm="HS256")

        # Мокаем TokenPayload
        mock_token_instance = MagicMock()
        mock_token_instance.exp = future_time
        mock_token_payload.return_value = mock_token_instance

        result = verify_token(token)

        assert result is not None
        mock_token_payload.assert_called_once()

    @patch("backend.core.security.settings")
    def test_verify_token_invalid_token(self, mock_settings):
        """Тест верификации невалидного токена"""
        mock_settings.SECURITY.JWT_SECRET_KEY = "test_secret_key"
        mock_settings.SECURITY.ALGORITHM = "HS256"

        invalid_token = "invalid.token.here"

        result = verify_token(invalid_token)

        assert result is None

    @patch("backend.core.security.settings")
    def test_verify_token_missing_sub(self, mock_settings):
        """Тест верификации токена без поля sub"""
        mock_settings.SECURITY.JWT_SECRET_KEY = "test_secret_key"
        mock_settings.SECURITY.ALGORITHM = "HS256"

        # Токен без sub
        payload = {
            "exp": int((datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp())
        }
        token = jwt.encode(payload, "test_secret_key", algorithm="HS256")

        result = verify_token(token)

        assert result is None

    @patch("backend.core.security.settings")
    def test_verify_token_missing_exp(self, mock_settings):
        """Тест верификации токена без поля exp"""
        mock_settings.SECURITY.JWT_SECRET_KEY = "test_secret_key"
        mock_settings.SECURITY.ALGORITHM = "HS256"

        # Токен без exp
        payload = {"sub": "test_user"}
        token = jwt.encode(payload, "test_secret_key", algorithm="HS256")

        result = verify_token(token)

        assert result is None

    @patch("backend.core.security.settings")
    @patch("backend.core.security.TokenPayload")
    def test_verify_token_expired(self, mock_token_payload, mock_settings):
        """Тест верификации истекшего токена"""
        mock_settings.SECURITY.JWT_SECRET_KEY = "test_secret_key"
        mock_settings.SECURITY.ALGORITHM = "HS256"

        # Создаем истекший токен
        past_time = datetime.now(timezone.utc) - timedelta(minutes=30)
        payload = {"sub": "test_user", "exp": int(past_time.timestamp())}
        token = jwt.encode(payload, "test_secret_key", algorithm="HS256")

        # Мокаем TokenPayload
        mock_token_instance = MagicMock()
        mock_token_instance.exp = past_time
        mock_token_payload.return_value = mock_token_instance

        result = verify_token(token)

        assert result is None


class TestOTP:
    """Тесты для функций работы с OTP"""

    @patch("backend.core.security.settings")
    def test_generate_otp_default_length(self, mock_settings):
        """Тест генерации OTP с дефолтной длиной"""
        mock_settings.SECURITY.OTP_LENGTH = 6  # Исправляем опечатку OTP*LENGTH

        otp = generate_otp()

        assert isinstance(otp, str)
        assert len(otp) == 6
        assert otp.isdigit()

    def test_generate_otp_custom_length(self):
        """Тест генерации OTP с кастомной длиной"""
        length = 8
        otp = generate_otp(length)

        assert isinstance(otp, str)
        assert len(otp) == length
        assert otp.isdigit()

    def test_generate_otp_different_each_time(self):
        """Тест что генерируются разные OTP коды"""
        otp1 = generate_otp(6)
        otp2 = generate_otp(6)

        # Вероятность получить одинаковые коды крайне мала
        assert otp1 != otp2 or len(set([generate_otp(6) for _ in range(10)])) > 1

    @patch("backend.core.security.settings")
    def test_get_otp_hash(self, mock_settings):
        """Тест получения хеша OTP"""
        mock_settings.SECURITY.HMAC_SECRET_KEY = "test_secret_key"

        otp = "123456"
        otp_hash = get_otp_hash(otp)

        assert isinstance(otp_hash, str)
        assert len(otp_hash) == 64  # SHA256 hex digest длина

        # Проверяем что хеш вычисляется правильно
        expected_hash = hmac.new(
            "test_secret_key".encode("utf-8"), otp.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        assert otp_hash == expected_hash

    @patch("backend.core.security.settings")
    def test_verify_otp_hash_valid(self, mock_settings):
        """Тест верификации валидного OTP хеша"""
        mock_settings.SECURITY.HMAC_SECRET_KEY = "test_secret_key"

        otp = "123456"
        otp_hash = get_otp_hash(otp)

        result = verify_otp_hash(otp, otp_hash)

        assert result is True

    @patch("backend.core.security.settings")
    def test_verify_otp_hash_invalid(self, mock_settings):
        """Тест верификации невалидного OTP хеша"""
        mock_settings.SECURITY.HMAC_SECRET_KEY = "test_secret_key"

        otp = "123456"
        wrong_otp = "654321"
        otp_hash = get_otp_hash(otp)

        result = verify_otp_hash(wrong_otp, otp_hash)

        assert result is False

    @patch("backend.core.security.settings")
    def test_get_otp_expiry_time_default(self, mock_settings):
        """Тест получения времени истечения OTP с дефолтными настройками"""
        mock_settings.SECURITY.OTP_EXPIRE_MINUTES = 5

        before_call = datetime.now(timezone.utc)
        expiry_time = get_otp_expiry_time()
        after_call = datetime.now(timezone.utc)

        expected_min = before_call + timedelta(minutes=5)
        expected_max = after_call + timedelta(minutes=5)

        assert expected_min <= expiry_time <= expected_max

    def test_get_otp_expiry_time_custom(self):
        """Тест получения времени истечения OTP с кастомными минутами"""
        minutes = 10

        before_call = datetime.now(timezone.utc)
        expiry_time = get_otp_expiry_time(minutes)
        after_call = datetime.now(timezone.utc)

        expected_min = before_call + timedelta(minutes=minutes)
        expected_max = after_call + timedelta(minutes=minutes)

        assert expected_min <= expiry_time <= expected_max

    def test_is_otp_valid_not_expired(self):
        """Тест что OTP валиден если не истек"""
        future_time = datetime.now(timezone.utc) + timedelta(minutes=5)

        result = is_otp_valid(future_time)

        assert result is True

    def test_is_otp_valid_expired(self):
        """Тест что OTP не валиден если истек"""
        past_time = datetime.now(timezone.utc) - timedelta(minutes=5)

        result = is_otp_valid(past_time)

        assert result is False

    def test_is_otp_valid_exactly_now(self):
        """Тест граничного случая когда OTP истекает прямо сейчас"""
        now = datetime.now(timezone.utc)

        result = is_otp_valid(now)

        # Должен быть False так как используется строгое сравнение <
        assert result is False


class TestIntegration:
    """Интеграционные тесты для проверки взаимодействия функций"""

    @patch("backend.core.security.settings")
    def test_full_otp_flow(self, mock_settings):
        """Тест полного флоу работы с OTP"""
        mock_settings.SECURITY.HMAC_SECRET_KEY = "test_secret_key"
        mock_settings.SECURITY.OTP_LENGTH = 6
        mock_settings.SECURITY.OTP_EXPIRE_MINUTES = 5

        # Генерируем OTP
        otp = generate_otp()

        # Получаем хеш
        otp_hash = get_otp_hash(otp)

        # Получаем время истечения
        expiry_time = get_otp_expiry_time()

        # Проверяем что OTP валиден
        assert verify_otp_hash(otp, otp_hash) is True
        assert is_otp_valid(expiry_time) is True

        # Проверяем что неправильный OTP не проходит
        wrong_otp = "000000"
        assert verify_otp_hash(wrong_otp, otp_hash) is False

    @patch("backend.core.security.settings")
    def test_full_jwt_flow(self, mock_settings):
        """Тест полного флоу работы с JWT"""
        mock_settings.SECURITY.JWT_SECRET_KEY = "test_secret_key"
        mock_settings.SECURITY.ALGORITHM = "HS256"
        mock_settings.SECURITY.ACCESS_TOKEN_EXPIRE_MINUTES = 60

        # Создаем токен
        user_data = {"sub": "test_user", "user_id": 123}
        token = create_access_token(user_data)

        # Верифицируем токен
        with patch("backend.core.security.TokenPayload") as mock_token_payload:
            mock_token_instance = MagicMock()
            mock_token_instance.exp = datetime.now(timezone.utc) + timedelta(minutes=30)
            mock_token_payload.return_value = mock_token_instance

            verified_token = verify_token(token)

            assert verified_token is not None


if __name__ == "__main__":
    pytest.main([__file__])
