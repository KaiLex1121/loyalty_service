from typing import Any, Dict, Optional


class BaseCustomException(Exception):
    """Базовое исключение для всех кастомных исключений приложения"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail or message
        self.headers = headers
        super().__init__(self.message)
