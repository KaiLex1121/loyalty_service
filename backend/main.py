import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

from backend.api.v1.api import api_router_v1
from backend.core.settings import settings
from backend.dao.holder import HolderDAO
from backend.db.session import create_pool

logging.basicConfig(
    level=logging.INFO,
    format="%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)
logger.level = logging.INFO


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup")
    yield
    logger.info("Application shutdown")


def create_app():
    templates = Jinja2Templates(directory=str(settings.WEB_APP.TEMPLATES_DIR))
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
    app.state.templates = templates

    return app


app = create_app()
