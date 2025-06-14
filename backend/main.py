from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api.v1.api import api_router_v1
from backend.core.exception_handlers import setup_exception_handlers
from backend.core.logger import get_logger
from backend.core.settings import settings
from backend.dao.holder import HolderDAO
from backend.db.session import create_pool

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup")
    yield
    logger.info("Application shutdown")


def create_app():
    pool = create_pool(settings)
    dao = HolderDAO()
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

    app.state.dao = dao
    app.state.pool = pool
    setup_exception_handlers(app)

    return app


app = create_app()
