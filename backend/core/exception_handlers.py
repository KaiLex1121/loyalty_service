from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from backend.core.logger import get_logger
from backend.exceptions.base import (
    BaseCustomException,
)

logger = get_logger(__name__)


async def custom_exception_handler(
    request: Request, exc: BaseCustomException
) -> JSONResponse:
    """
    Обработчик кастомных исключений для FastAPI
    """
    logger.error(
        f"Custom exception occurred: {exc.__class__.__name__} - {exc.message}",
        extra={
            "exception_type": exc.__class__.__name__,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers
    )


def setup_exception_handlers(app: FastAPI):
    app.add_exception_handler(BaseCustomException, custom_exception_handler)
