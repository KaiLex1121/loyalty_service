from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from backend.api.v1.api import api_router_v1
from backend.core.exception_handlers import setup_exception_handlers
from backend.core.logger import get_logger
from backend.core.security import oauth2_scheme_backoffice
from backend.core.settings import settings

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
        openapi_components={
            "securitySchemes": {"BackofficeBearerAuth": oauth2_scheme_backoffice.model}
        },
    )
    app.include_router(api_router_v1, prefix="/api/v1")
    setup_exception_handlers(app)

    return app


app = create_app()
