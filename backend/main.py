import logging
from pathlib import Path
from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from backend.core.config import settings

def create_app():


    app = FastAPI(

    )

    app.mount(
        "/static",
        StaticFiles(directory=settings.WEB_APP.STATIC_DIR),
        name="static",
    )
    return app


templates = Jinja2Templates(directory=settings.WEB_APP.TEMPLATES_DIR)
app = create_app()



@app.get("/", response_class=HTMLResponse, tags=["Root"])
async def read_root(request: Request):
    """
    Простой HTML ответ для проверки работы Jinja2 и FastAPI.
    Это будет заменено на главную страницу бэк-офиса.
    """
    # В будущем здесь будет проверка аутентификации
    # и редирект на логин или на дашборд
    return templates.TemplateResponse(
        "index.html", # Предполагается, что такой файл есть
        {"request": request, "message": "Добро пожаловать в сервис лояльности!"}
    )