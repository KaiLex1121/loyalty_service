from decimal import Decimal

import httpx
import pybreaker
from app.core.settings import settings

# CircuitBreaker: откроется на 60 секунд после 5 последовательных сбоев
breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60)


class CoreApiClient:
    def __init__(self):
        self.base_url = f"{settings.API.INTERNAL_CORE_BASE_URL}/api/v1"
        self.base_headers = {"X-Internal-API-Key": settings.API.INTERNAL_KEY}
        self.client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        """Закрывает httpx.AsyncClient (например, при завершении приложения)."""
        await self.client.aclose()

    def _merge_headers(self, headers: dict | None = None) -> dict:
        """Объединяет базовые заголовки с дополнительными."""
        return {**self.base_headers, **(headers or {})}

    @breaker
    async def _request(self, method: str, path: str, **kwargs):
        """Единый защищённый метод для всех HTTP-запросов к Core API."""
        kwargs["headers"] = self._merge_headers(kwargs.pop("headers", None))

        try:
            response = await self.client.request(
                method, f"{self.base_url}{path}", **kwargs
            )
            if response.status_code == 404:
                return None

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise pybreaker.CircuitBreakerError(
                f"API call failed with status {e.response.status_code}"
            )
        except httpx.RequestError as e:
            raise pybreaker.CircuitBreakerError(f"Network error during API call: {e}")

    async def _get(self, path: str, **kwargs):
        return await self._request("GET", path, **kwargs)

    async def _post(self, path: str, **kwargs):
        return await self._request("POST", path, **kwargs)

    # --- Публичные методы ---

    async def get_active_bots(self):
        return await self._get("/internal/telegram-bots/active")

    async def get_customer_profile(self, telegram_id: int, company_id: int):
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
        return await self._get(f"/internal/customers/{customer_role_id}/transactions")

    async def get_active_promotions(self, company_id: int):
        return await self._get(
            "/internal/customers/promotions", params={"company_id": company_id}
        )

    async def request_employee_otp(self, phone_number: str, company_id: int):
        payload = {"work_phone_number": phone_number}
        return await self._post(
            "/internal/employees/auth/request-otp",
            params={"company_id": company_id},
            json=payload,
        )

    async def verify_employee_otp(
        self, phone_number: str, otp_code: str, company_id: int
    ):
        payload = {"work_phone_number": phone_number, "otp_code": otp_code}
        return await self._post(
            "/internal/employees/auth/verify-otp",
            params={"company_id": company_id},
            json=payload,
        )

    async def find_customer(self, employee_jwt: str, phone_number: str):
        return await self._get(
            "/internal/employees/find-customer",
            headers={"Authorization": f"Bearer {employee_jwt}"},
            params={"phone_number": phone_number},
        )

    async def select_employee_outlet(
        self, phone_number: str, outlet_id: int, company_id: int
    ):
        payload = {"phone_number": phone_number, "outlet_id": outlet_id}
        return await self._post(
            "/internal/employees/auth/select-outlet",
            params={"company_id": company_id},
            json=payload,
        )

    async def accrue_cashback(
        self, employee_jwt: str, customer_role_id: int, amount: Decimal
    ):
        """
        Выполняет начисление кэшбэка клиенту от имени сотрудника.
        """
        payload = {"customer_role_id": customer_role_id, "purchase_amount": str(amount)}
        request_headers = {"Authorization": f"Bearer {employee_jwt}"}
        return await self._post(
            "/internal/employees/operations/accrue-cashback",
            headers=request_headers,
            json=payload,
        )
