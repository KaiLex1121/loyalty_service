from contextlib import asynccontextmanager

from app.api.v1.api import api_router_v1
from app.broker import faststream_router
from app.core.exception_handlers import setup_exception_handlers
from app.core.logger import get_logger
from app.core.settings import settings
from fastapi import FastAPI

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup")
    yield
    logger.info("Application shutdown")


def create_app():
    app = FastAPI(
        title=settings.API.TITLE,
        openapi_url=settings.API.OPENAPI_URL,
        docs_url=settings.API.DOCS_URL,
        redoc_url=settings.API.REDOC_URL,
        version=settings.API.VERSION,
        debug=settings.API.DEBUG,
        lifespan=lifespan,
    )
    app.include_router(api_router_v1, prefix="/api/v1")
    app.include_router(faststream_router)

    setup_exception_handlers(app)

    return app


app = create_app()
