import json
import logging
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import Update
from aiohttp import request
from app.api_client import CoreApiClient
from app.bots.customer_bot.handlers import setup_customer_bot_handlers
from app.bots.employee_bot.handlers import setup_employee_bot_handlers
from app.bots.shared.middlewares import setup_shared_middlewares
from app.broker import faststream_router
from app.cache_client import CacheClient
from app.core.settings import settings
from fastapi import Depends, FastAPI, HTTPException, Request
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from shared.schemas.schemas import BotInfo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_cache_client = CacheClient()
_core_api_client = CoreApiClient()


def create_dispatcher() -> Dispatcher:
    fsm_storage = RedisStorage(_cache_client.redis)
    dp = Dispatcher(storage=fsm_storage)

    setup_customer_bot_handlers(dp)
    setup_employee_bot_handlers(dp)
    setup_shared_middlewares(
        dp, cache_client=_cache_client, api_client=_core_api_client
    )

    return dp


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Инициализация клиентов
    app.state.api_client = _core_api_client
    app.state.cache_client = _cache_client
    app.state.bots = {}

    try:
        active_bots_data = await app.state.api_client.get_active_bots()
        for bot_data in active_bots_data:
            bot_info = BotInfo(**bot_data)
            await app.state.cache_client.set_bot_info(bot_info)
            bot = Bot(token=bot_info.token)

            webhook_url = (
                f"{settings.API.GATEWAY_BASE_URL}/telegram/bot{bot_info.token}"
            )

            await bot.set_webhook(webhook_url, drop_pending_updates=True)
            app.state.bots[bot_info.token] = Bot(
                token=bot_info.token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML)
            )

            await bot.session.close()

    except Exception as e:
        logger.error(f"Failed to initialize cache client: {e}", exc_info=True)

    yield
    await app.state.cache_client.close()
    await app.state.api_client.close()


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
    app = FastAPI(title="Telegram Bot Gateway", lifespan=lifespan)
    app.include_router(faststream_router)
    return app


app = create_app()
dp = create_dispatcher()


# --- 4. HTTP маршруты ---
@app.post("/telegram/bot{token}")
async def telegram_webhook(
    token: str, request: Request, cache: CacheClient = Depends(get_cache_client)
):
    """Обработка вебхуков от Telegram"""
    bot_info = await cache.get_bot_info(token)
    if not bot_info:
        raise HTTPException(
            status_code=404, detail="Bot not registered or cache expired"
        )
    update_data = await request.json()
    if token not in request.app.state.bots:
        new_bot = Bot(
            token=token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        request.app.state.bots[token] = new_bot
    bot = request.app.state.bots[token]
    update = Update.model_validate(update_data, context={"bot": bot})

    try:
        await dp.feed_webhook_update(bot, update)
    except Exception as e:
        update_id = update_data.get("update_id")
        logger.error(
            f"Failed to process update id={update_id} for bot ...{token[-4:]}: {e}",
            exc_info=True,
        )
    finally:
        await bot.session.close()

    return {"status": "ok"}
