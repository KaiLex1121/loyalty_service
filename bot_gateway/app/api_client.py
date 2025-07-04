import httpx
import pybreaker
from app.core.settings import settings

# Создаем "предохранитель": откроется на 60 секунд после 5 сбоев подряд
breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60)

class CoreApiClient:
    def __init__(self):
        self.base_url = settings.API.INTERNAL_CORE_BASE_URL
        self.headers = {"X-Internal-API-Key": settings.API.INTERNAL_KEY}

    @breaker
    async def get_active_bots(self):
        """Запрос, защищенный предохранителем."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/internal/bots/active",
                    headers=self.headers,
                    timeout=5.0 # Важно ставить таймауты
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                # Перехватываем ошибку и пробрасываем ее как pybreaker.CircuitBreakerError
                # чтобы "предохранитель" засчитал ее как сбой
                raise pybreaker.CircuitBreakerError(f"API call failed: {e.response.status_code}")
            except httpx.RequestError as e:
                raise pybreaker.CircuitBreakerError(f"Network error: {e}")