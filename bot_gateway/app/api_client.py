import httpx
import pybreaker
from app.core.settings import settings

# Создаем "предохранитель": откроется на 60 секунд после 5 последовательных сбоев.
# Этот экземпляр будет общим для всех вызовов из этого клиента.
breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60)


class CoreApiClient:
    def __init__(self):
        self.base_url = settings.API.INTERNAL_CORE_BASE_URL
        self.headers = {"X-Internal-API-Key": settings.API.INTERNAL_KEY}

    @breaker
    async def _request(self, method: str, path: str, **kwargs):
        """
        Единый защищенный метод для всех HTTP-запросов к Core API.
        Обернут в Circuit Breaker для отказоустойчивости.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=f"{self.base_url}/api/v1{path}",
                    headers=self.headers,
                    timeout=10.0,
                    **kwargs,
                )

                # Специальная обработка 404 - это не сбой, а "не найдено"
                if response.status_code == 404:
                    return None

                # Для всех остальных ошибок (4xx, 5xx) выбрасываем исключение
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                # Ошибка HTTP-статуса (напр., 500, 403). Считается сбоем для "предохранителя".
                raise pybreaker.CircuitBreakerError(
                    f"API call failed with status {e.response.status_code}"
                )
            except httpx.RequestError as e:
                # Ошибка сети (не удалось подключиться, таймаут). Тоже сбой.
                raise pybreaker.CircuitBreakerError(
                    f"Network error during API call: {e}"
                )

    async def _get(self, path: str, **kwargs):
        """Вспомогательная обертка для GET-запросов."""
        return await self._request("GET", path, **kwargs)

    async def _post(self, path: str, **kwargs):
        """Вспомогательная обертка для POST-запросов."""
        return await self._request("POST", path, **kwargs)

    # --- Публичные методы ---

    async def get_active_bots(self):
        """Получает список всех активных ботов для инициализации шлюза."""
        return await self._get("/internal/telegram-bots/active")

    async def get_customer_profile(self, telegram_id: int, company_id: int):
        """Получает профиль клиента по Telegram ID в рамках компании."""
        return await self._get(
            f"/internal/customers/by-telegram-id/{telegram_id}",
            params={"company_id": company_id},
        )

    async def onboard_customer(
        self,
        telegram_id: int,
        phone_number: str,
        company_id: int,
        full_name: str | None,
    ):
        """Регистрирует нового клиента."""
        payload = {
            "telegram_user_id": telegram_id,
            "phone_number": phone_number,
            "full_name": full_name,
        }
        return await self._post(
            "/internal/customers/onboard",
            params={"company_id": company_id},
            json=payload,
        )

    async def get_transaction_history(self, customer_role_id: int):
        """Получает историю транзакций клиента."""
        return await self._get(f"/internal/customers/{customer_role_id}/transactions")

    async def get_active_promotions(self, company_id: int):
        """Получает активные акции для компании."""
        return await self._get(
            "/internal/customers/promotions", params={"company_id": company_id}
        )

    async def request_employee_otp(self, phone_number: str, company_id: int):
        """Запрашивает OTP для входа сотрудника."""
        payload = {"work_phone_number": phone_number}
        return await self._post(
            "/internal/employees/auth/request-otp",
            params={"company_id": company_id},
            json=payload,
        )

    async def verify_employee_otp(
        self, phone_number: str, otp_code: str, company_id: int
    ):
        """Проверяет OTP и получает JWT для сотрудника."""
        payload = {"work_phone_number": phone_number, "otp_code": otp_code}
        return await self._post(
            "/internal/employees/auth/verify-otp",
            params={"company_id": company_id},
            json=payload,
        )
