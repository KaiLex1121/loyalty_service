from contextlib import asynccontextmanager
import logging
from pathlib import Path
from fastapi import Depends, FastAPI, APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from backend.core.settings import get_config
from backend.core.dependencies import get_jinja_templates
from backend.dao.holder import HolderDAO
from backend.db.session import create_pool
from backend.core.settings import settings
from backend.api.v1.api import api_router_v1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup: Creating database tables if they don't exist...")
    yield
    logger.info("Application shutdown")


def create_app():
    templates = Jinja2Templates(directory=str(settings.WEB_APP.TEMPLATES_DIR))
    pool = create_pool(settings)
    dao = HolderDAO()
    app = FastAPI(
        title=settings.API.TITLE,
        openapi_prefix=settings.API.PREFIX,
        docs_url=settings.API.DOCS_URL,
        redoc_url=settings.API.REDOC_URL,
        version=settings.API.VERSION,
        openapi_url=settings.API.OPENAPI_URL,
        debug=settings.API.DEBUG,
        lifespan=lifespan
    )
    app.include_router(api_router_v1, prefix="/api/v1")
    app.state.dao = dao
    app.state.pool = pool
    app.state.templates = templates
    app.mount(
        "/static",
        StaticFiles(directory=settings.WEB_APP.STATIC_DIR),
        name="static",
    )

    return app



app = create_app()



@app.get("/", response_class=HTMLResponse, tags=["Root"])
async def read_root(request: Request, templates: Jinja2Templates = Depends(get_jinja_templates) ):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "message": "Добро пожаловать в сервис лояльности!"}
    )