from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from backend.core.logger import get_logger
from backend.exceptions.base import (
    AccountNotFoundError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)

logger = get_logger(__name__)


def setup_exception_handlers(app: FastAPI):

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)}
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc)},
        )

    @app.exception_handler(PermissionDeniedError)
    async def permission_denied_handler(request: Request, exc: PermissionDeniedError):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN, content={"detail": str(exc)}
        )

    @app.exception_handler(AccountNotFoundError)
    async def account_not_found_handler(request: Request, exc: AccountNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": str(exc)}
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        """Обработчик для всех остальных (системных) исключений"""
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
