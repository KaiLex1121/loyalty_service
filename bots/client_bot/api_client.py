# Файл `api_client.py` (или модуль, если он разрастется) в каждом из ваших ботов (`client_bot` и `employee_bot`) должен инкапсулировать всю логику взаимодействия с вашим бэкенд API. Его основная задача — предоставить удобные, типизированные функции для отправки запросов к API и обработки ответов.

# Вот что обычно должно быть в `api_client.py`:

# 1.  **Базовый URL API и конфигурация клиента:**
#     *   Константа или переменная, хранящая базовый URL вашего API (например, `http://localhost:8000/api/v1/` или `https://your-loyalty-api.com/api/v1/`). Лучше всего загружать это из конфигурационного файла бота (`config.py`).
#     *   Инициализация HTTP-клиента. Для асинхронных ботов на Aiogram идеально подходит `httpx.AsyncClient` или `aiohttp.ClientSession`.
#     *   Настройка таймаутов, заголовков по умолчанию (например, `Content-Type: application/json`), возможно, обработка SSL-сертификатов для продакшена.

# 2.  **Функции для каждого эндпоинта API:**
#     *   Для каждого эндпоинта вашего бэкенд API должна быть соответствующая функция в `api_client.py`.
#     *   **Именование:** Имена функций должны быть говорящими и отражать действие, которое они выполняют (например, `get_client_balance`, `accrue_cashback_points`, `create_company_employee`).
#     *   **Типизация аргументов и возвращаемых значений:** Используйте Pydantic схемы из `shared/schemas/` для типизации данных, передаваемых в API (тела запросов, параметры пути/запроса) и данных, получаемых из API (тела ответов). Это делает код более надежным и понятным.
#     *   **Формирование URL:** Функции должны корректно формировать полный URL для запроса, используя базовый URL и специфичные пути эндпоинтов.
#     *   **Отправка запроса:** Использование выбранного HTTP-клиента для отправки запроса (GET, POST, PUT, DELETE и т.д.).
#     *   **Обработка ответа:**
#         *   Проверка статус-кода ответа.
#         *   Парсинг JSON-ответа в Pydantic схемы (если ответ успешен и содержит данные).
#         *   Обработка ошибок API (например, 4xx, 5xx коды). Это может включать логирование ошибки, возврат `None` или специального объекта ошибки, или даже проброс кастомного исключения, которое затем будет обработано в хендлерах бота.

# 3.  **Аутентификация (если требуется для API):**
#     *   Если API требует аутентификации (например, JWT-токены для сотрудников), `api_client.py` должен уметь:
#         *   Прикреплять токен к запросам (обычно в заголовке `Authorization`).
#         *   Возможно, иметь функцию для получения/обновления токена (например, `login_employee_and_get_token`).
#         *   Безопасно хранить и управлять токеном (хотя само хранение токена может быть делегировано другому компоненту бота, например, FSM-контексту или какому-то хранилищу состояний).

# 4.  **Обработка ошибок сети и API:**
#     *   Предусмотреть обработку сетевых ошибок (например, `httpx.RequestError`).
#     *   Решить, как будут обрабатываться ошибки API: будут ли они просто логироваться и функция вернет `None`, или будут возбуждаться кастомные исключения, которые хендлеры бота смогут отлавливать и соответствующим образом реагировать (например, показывать пользователю сообщение об ошибке).

# **Пример структуры файла `bots/client_bot/api_client.py`:**

# ```python
# import httpx
# from typing import Optional, List, Dict, Any
# from logging import getLogger

# # Импорт схем из общего модуля
# from common.schemas.client import ClientSchema, ClientCreateSchema
# from common.schemas.transaction import TransactionSchema, TransactionCreateSchema
# from common.schemas.feedback import FeedbackCreateSchema, FeedbackSchema

# # Импорт конфигурации бота (где может быть API_BASE_URL)
# from ..config import settings # Предполагая, что settings - это Pydantic BaseSettings или объект с API_URL

# logger = getLogger(__name__)

# API_BASE_URL = settings.API_BASE_URL # Например, "http://localhost:8000/api/v1"

# # Можно создать один экземпляр клиента для всего модуля, если это безопасно
# # или создавать его в каждой функции/менеджере контекста
# # async_client = httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0)


# async def _make_request(
#     method: str,
#     endpoint: str,
#     params: Optional[Dict[str, Any]] = None,
#     json_data: Optional[Dict[str, Any]] = None,
#     expected_status: int = 200,
#     # token: Optional[str] = None # Если нужна аутентификация
# ) -> Optional[Dict[str, Any]]:
#     """Вспомогательная функция для выполнения запросов."""
#     headers = {"Content-Type": "application/json"}
#     # if token:
#     #     headers["Authorization"] = f"Bearer {token}"

#     try:
#         async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0) as client:
#             response = await client.request(
#                 method,
#                 endpoint,
#                 params=params,
#                 json=json_data,
#                 headers=headers
#             )

#         if response.status_code == expected_status:
#             if response.content:
#                 return response.json()
#             return {} # Для ответов без тела, но с корректным статусом (e.g., 204 No Content)
#         else:
#             logger.error(
#                 f"API request to {endpoint} failed with status {response.status_code}: {response.text}"
#             )
#             # Здесь можно добавить более специфичную обработку ошибок или выбросить исключение
#             return None
#     except httpx.RequestError as e:
#         logger.error(f"Network error during API request to {endpoint}: {e}")
#         return None
#     except Exception as e:
#         logger.error(f"Unexpected error during API request to {endpoint}: {e}")
#         return None


# # --- Функции для эндпоинтов, связанных с клиентами ---

# async def get_or_create_client_by_telegram_id(telegram_id: int, username: Optional[str] = None) -> Optional[ClientSchema]:
#     """Получает или создает клиента по Telegram ID."""
#     payload = {"telegram_id": telegram_id}
#     if username:
#         payload["username"] = username

#     response_data = await _make_request(
#         method="POST",
#         endpoint="/clients/get_or_create/", # Пример эндпоинта
#         json_data=payload,
#         expected_status=200 # Или 201, если создание всегда возвращает 201
#     )
#     if response_data is not None:
#         return ClientSchema(**response_data)
#     return None

# async def get_client_balance(client_id: int) -> Optional[float]: # Или схема с балансом
#     """Получает баланс кэшбэка клиента."""
#     response_data = await _make_request(
#         method="GET",
#         endpoint=f"/clients/{client_id}/balance/"
#     )
#     if response_data is not None and "balance" in response_data:
#         return float(response_data["balance"])
#     return None

# async def get_client_transactions(client_id: int) -> List[TransactionSchema]:
#     """Получает историю транзакций клиента."""
#     response_data = await _make_request(
#         method="GET",
#         endpoint=f"/clients/{client_id}/transactions/"
#     )
#     if response_data is not None:
#         return [TransactionSchema(**item) for item in response_data]
#     return []

# async def submit_feedback(client_id: int, feedback_data: FeedbackCreateSchema) -> Optional[FeedbackSchema]:
#     """Отправляет обратную связь от клиента."""
#     response_data = await _make_request(
#         method="POST",
#         endpoint=f"/clients/{client_id}/feedback/",
#         json_data=feedback_data.model_dump(),
#         expected_status=201
#     )
#     if response_data is not None:
#         return FeedbackSchema(**response_data)
#     return None

# # --- Функции для эндпоинтов, связанных с сотрудниками (в employee_bot/api_client.py) ---
# # async def identify_client_by_phone(phone_number: str, employee_token: str) -> Optional[ClientSchema]: ...
# # async def accrue_cashback(data: TransactionCreateSchema, employee_token: str) -> Optional[TransactionSchema]: ...
# # async def redeem_cashback(data: TransactionCreateSchema, employee_token: str) -> Optional[TransactionSchema]: ...
# ```

# **Преимущества такого подхода:**

# *   **Инкапсуляция:** Вся логика общения с API скрыта внутри этого модуля. Хендлеры бота просто вызывают эти функции.
# *   **Переиспользование:** Функции можно вызывать из разных хендлеров.
# *   **Тестируемость:** Модуль `api_client.py` можно тестировать отдельно (мокая HTTP-запросы). Хендлеры также легче тестировать, мокая вызовы функций из `api_client.py`.
# *   **Читаемость:** Хендлеры становятся чище, так как не содержат низкоуровневого кода для HTTP-запросов.
# *   **Централизованное управление ошибками:** Обработка ошибок API и сети происходит в одном месте.
# *   **Типобезопасность:** Использование Pydantic схем помогает избежать ошибок, связанных с неправильной структурой данных.

# Этот модуль становится критически важным связующим звеном между вашими ботами и бэкендом.