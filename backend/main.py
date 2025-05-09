import logging
from fastapi import FastAPI, APIRouter
from app.config.main_config import load_config
from app.routers.root import root_router


def create_app():
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.INFO,
        format="%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s",
    )
    app = FastAPI()
    app.include_router(root_router)
    return app


log_level = logging.INFO
