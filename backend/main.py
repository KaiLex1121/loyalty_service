from contextlib import asynccontextmanager
import logging
from pathlib import Path
from fastapi import Depends, FastAPI, APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from backend.core.config import get_config
from backend.core.dependencies import get_jinja_templates
from backend.db.session import create_pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    config = get_config()
    templates = Jinja2Templates(directory=str(config.WEB_APP.TEMPLATES_DIR))
    pool = create_pool(config)

    app.state.config = config
    app.state.pool = pool
    app.state.templates = templates
    yield


def create_app():
    config = get_config()
    app = FastAPI(
        lifespan=lifespan,
    )
    app.mount(
        "/static",
        StaticFiles(directory=config.WEB_APP.STATIC_DIR),
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