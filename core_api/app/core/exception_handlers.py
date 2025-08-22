from app.core.logger import get_logger
from app.exceptions.base import BaseAppException
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = get_logger(__name__)


async def base_app_exception_handler(
    request: Request, exc: BaseAppException
) -> JSONResponse:
    """
    Обработчик для BaseAppException и его наследников.
    Логирует internal_details, если они есть.
    """
    content = {"detail": exc.detail}
    if exc.internal_details:
        logger.error(
            f"Application error: {exc.detail} "
            f"| Path: {request.url.path} | Method: {request.method} "
            f"| Internal Details: {exc.internal_details}"
        )
    else:
        logger.warning(
            f"Application warning: {exc.detail} "
            f"| Path: {request.url.path} | Method: {request.method}"
        )

    headers = getattr(
        exc, "headers", None
    )  # Для UnauthorizedException с WWW-Authenticate
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=headers,
    )


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Обработчик для ошибок валидации Pydantic (RequestValidationError).
    Форматирует ошибки для более читаемого ответа.
    """
    errors = []
    for error in exc.errors():
        field = " -> ".join(map(str, error["loc"]))
        message = error["msg"]
        errors.append({"field": field, "message": message})

    logger.warning(
        f"Request validation error: {errors} "
        f"| Path: {request.url.path} | Method: {request.method} "
        f"| Body: {await request.body()}"
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": "Validation Error", "errors": errors}),
    )


async def pydantic_validation_error_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """
    Обработчик для pydantic.ValidationError, если они возникают в сервисах
    и не были обернуты в кастомные исключения.
    """
    errors = []
    for error in exc.errors():
        field = " -> ".join(map(str, error.get("loc", ["unknown_location"])))
        message = error.get("msg", "Unknown error")
        errors.append({"field": field, "message": message})

    logger.error(
        f"Pydantic validation error in application logic: {errors} "
        f"| Path: {request.url.path} | Method: {request.method}",
        exc_info=True,  # Добавляем stack trace
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # Это ошибка сервера, если Pydantic падает не на входе
        content=jsonable_encoder(
            {
                "detail": "An internal validation error occurred.",
                "errors": errors,  # Можно скрыть в продакшене
            }
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Глобальный обработчик для всех необработанных исключений.
    Логирует ошибку и возвращает стандартизированный ответ 500.
    """
    logger.error(
        f"Unhandled exception: {exc} "
        f"| Path: {request.url.path} | Method: {request.method}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred."},
    )


def setup_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(BaseAppException, base_app_exception_handler)  # type: ignore
    app.add_exception_handler(
        RequestValidationError, request_validation_exception_handler  # type: ignore
    )  #
    app.add_exception_handler(
        ValidationError, pydantic_validation_error_handler  # type: ignore
    )  # Для pydantic ошибок из сервисов
    app.add_exception_handler(
        Exception, unhandled_exception_handler
    )  # Этот должен быть последним
