from typing import Any, Dict, Optional

from fastapi import status


class BaseAppException(Exception):
    """
    Базовое исключение приложения.

    Атрибуты:
    status_code (int): HTTP статус код для ответа.
    detail (str): Сообщение об ошибке для клиента.
    internal_details (Optional[Dict[str, Any]]): Дополнительные детали для логирования,
                                                  которые не предназначены для клиента.
    """

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "An unexpected internal server error occurred."
    internal_details: Optional[Dict[str, Any]] = None

    def __init__(
        self,
        detail: Optional[str] = None,
        status_code: Optional[int] = None,
        internal_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.detail = detail or self.detail
        self.status_code = status_code or self.status_code
        self.internal_details = internal_details or {}
        super().__init__(self.detail)
