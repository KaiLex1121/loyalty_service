from backend.core.security import (
    create_access_token,
    generate_otp,
    get_otp_expiry_time,
    get_otp_hash,
    is_otp_valid,
    verify_otp_hash,
    verify_token,
)
from backend.core.settings import AppSettings


class TestIntegration:
    """Интеграционные тесты для проверки взаимодействия функций"""

    def test_full_otp_flow(self, test_settings: AppSettings):
        """Тест полного флоу работы с OTP"""
        # 1. Генерируем OTP
        otp = generate_otp(settings=test_settings)
        # 2. Получаем хеш
        otp_hash = get_otp_hash(otp=otp, settings=test_settings)
        # 3. Получаем время истечения
        expiry_time = get_otp_expiry_time(settings=test_settings)

        # 4. Проверяем, что все работает вместе
        assert (
            verify_otp_hash(
                otp_code=otp, hashed_otp_code=otp_hash, settings=test_settings
            )
            is True
        )
        assert is_otp_valid(expiry_time) is True

        wrong_otp = "000000"
        assert verify_otp_hash(wrong_otp, otp_hash, settings=test_settings) is False

    def test_full_jwt_flow(self, test_settings: AppSettings):
        """Тест полного флоу работы с JWT"""
        # 1. Создаем токен
        user_data = {"sub": "test_user_full_flow", "user_id": 123}
        token = create_access_token(data=user_data, settings=test_settings)
        # 2. Верифицируем токен
        verified_payload = verify_token(token=token, settings=test_settings)

        assert verified_payload is not None
        assert verified_payload.sub == "test_user_full_flow"
