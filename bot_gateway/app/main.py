from contextlib import asynccontextmanager
import json
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import FastAPI, Request, HTTPException, Depends
from app.core.settings import settings
from app.customer_bot.handlers.general import main_menu
from app.api_client import CoreApiClient
from app.cache import CacheClient
from app.customer_bot.middlewares.data_loader import LoadDataMiddleware
from shared.schemas.schemas import BotInfo
from app.broker import faststream_router
from app.subscribers import broadcast, bot_management


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp = Dispatcher()
dp.include_router(main_menu.router)
dp.update.middleware(LoadDataMiddleware())

@asynccontextmanager
async def lifespan(app: FastAPI):

    # Инициализация клиентов
    app.state.api_client = CoreApiClient()
    app.state.cache_client = CacheClient()

    try:
        active_bots_data = await app.state.api_client.get_active_bots()
        for bot_data in active_bots_data:
            bot_info = BotInfo(**bot_data)
            await app.state.cache_client.set_bot_info(bot_info)
            bot = Bot(token=bot_info.token)

            webhook_url = f"{settings.API.GATEWAY_BASE_URL}/telegram/bot{bot_info.token}"

            await bot.set_webhook(webhook_url, drop_pending_updates=True)
            await bot.session.close()

    except Exception as e:
        logger.error(f"Failed to initialize cache client: {e}", exc_info=True)

    yield
    await app.state.cache_client.close()


# --- 2. Зависимости для FastAPI и FastStream ---
def get_cache_client(request: Request) -> CacheClient:
    cache = request.app.state.cache_client
    if cache is None:
        raise HTTPException(status_code=500, detail="Cache client not initialized")
    return cache


def get_api_client(request: Request) -> CoreApiClient:
    api = request.app.state.api_client
    if api is None:
        raise HTTPException(status_code=500, detail="API client not initialized")
    return api


# --- 3. Создание приложения ---
def create_app():
    app = FastAPI(
        title="Telegram Bot Gateway",
        lifespan=lifespan
    )
    app.include_router(faststream_router)
    return app


app = create_app()

# --- 4. HTTP маршруты ---
@app.post("/telegram/bot{token}")
async def telegram_webhook(
    token: str,
    request: Request,
    cache: CacheClient = Depends(get_cache_client)
):
    """Обработка вебхуков от Telegram"""
    bot_info = await cache.get_bot_info(token)
    if not bot_info:
        raise HTTPException(
            status_code=404,
            detail="Bot not registered or cache expired"
        )
    update_data = await request.json()
    bot = Bot(token=token)
    update = Update.model_validate(update_data, context={"bot": bot})

    try:
        await dp.feed_webhook_update(bot, update)
    except Exception as e:
        update_id = update_data.get('update_id')
        logger.error(f"Failed to process update id={update_id} for bot ...{token[-4:]}: {e}", exc_info=True)
    finally:
        await bot.session.close()

    return {"status": "ok"}
