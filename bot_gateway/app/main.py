from contextlib import asynccontextmanager
from typing import Optional
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import FastAPI, Request, HTTPException, Depends
from app.core.settings import settings
from app.customer_bot.handlers.general import main_menu
from app.subscribers import broadcast  # Импортируем, чтобы подписчик зарегистрировался
from app.api_client import CoreApiClient
from app.cache import CacheClient
from shared.schemas.schemas import BotInfo
from app.broker import broker  # Импортируем брокер


# Создаем Dispatcher для Aiogram
dp = Dispatcher()
dp.include_router(main_menu.router)

class AppState:
    """Состояние приложения"""
    def __init__(self):
        self.cache_client: Optional[CacheClient] = None
        self.api_client: Optional[CoreApiClient] = None

    async def initialize(self):
        """Инициализация состояния"""
        self.api_client = CoreApiClient()
        self.cache_client = CacheClient()

    async def cleanup(self):
        """Очистка ресурсов"""
        if self.cache_client:
            # await self.cache_client.close()
            pass
        self.cache_client = None
        self.api_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    print("Starting application...")

    # Создаем и инициализируем состояние приложения
    app_state = AppState()
    await app_state.initialize()

    # Запускаем брокер
    await broker.start()

    # Сохраняем состояние в контексте приложения
    app.state.app_state = app_state

    try:
        # Получаем активных ботов и настраиваем вебхуки
        if app_state.api_client and app_state.cache_client:
            active_bots_data = await app_state.api_client.get_active_bots()
            for bot_data in active_bots_data:
                bot_info = BotInfo(**bot_data)
                await app_state.cache_client.set_bot_info(bot_info)

                bot = Bot(token=bot_info.token)
                webhook_url = f"{settings.API.GATEWAY_BASE_URL}/telegram/bot{bot_info.token}"
                await bot.set_webhook(webhook_url, drop_pending_updates=True)
                await bot.session.close()
                print(f"Webhook set for bot of company '{bot_info.company_name}'")
    except Exception as e:
        print(f"ERROR during startup: {e}")

    yield  # Приложение работает

    # Логика при выключении
    print("Shutting down application...")

    # Закрываем брокер
    await broker.close()

    # Очищаем состояние
    await app_state.cleanup()

    print("Application shutdown complete.")

def get_app_state(request: Request) -> AppState:
    """Dependency для получения состояния приложения"""
    return request.app.state.app_state

def get_cache_client(app_state: AppState = Depends(get_app_state)) -> CacheClient:
    """Dependency для получения кэш-клиента"""
    if app_state.cache_client is None:
        raise HTTPException(status_code=500, detail="Cache client not initialized")
    return app_state.cache_client

def get_api_client(app_state: AppState = Depends(get_app_state)) -> CoreApiClient:
    """Dependency для получения API-клиента"""
    if app_state.api_client is None:
        raise HTTPException(status_code=500, detail="API client not initialized")
    return app_state.api_client

def create_app():
    """Создание FastAPI приложения"""
    app = FastAPI(
        title="Telegram Bot Gateway",
        lifespan=lifespan
    )

    # Создаем и подключаем RabbitRouter
    rabbit_router = RabbitRouter()
    app.include_router(rabbit_router)

    return app

# Создаем приложение
app = create_app()

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

    try:
        await dp.feed_webhook_update(
            bot,
            Update.model_validate(update_data, context={"bot": bot}),
            company_id=bot_info.company_id,
            company_name=bot_info.company_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process update: {str(e)}")
    finally:
        await bot.session.close()

    return {"status": "ok"}

# @app.get("/health")
# async def health_check():
#     """Проверка здоровья приложения"""
#     return {"status": "ok", "message": "Bot gateway is running"}

# @app.get("/bots/active")
# async def get_active_bots(cache: CacheClient = Depends(get_cache_client)):
#     """Получение списка активных ботов"""
#     try:
#         bots = await cache.get_all_bots()
#         return {
#             "count": len(bots),
#             "bots": [
#                 {
#                     "company_id": bot.company_id,
#                     "company_name": bot.company_name,
#                     "token": bot.token[:10] + "..." if len(bot.token) > 10 else bot.token
#                 }
#                 for bot in bots
#             ]
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to get active bots: {str(e)}")

# @app.post("/bots/refresh")
# async def refresh_bots(
#     api_client: CoreApiClient = Depends(get_api_client),
#     cache: CacheClient = Depends(get_cache_client)
# ):
#     """Обновление списка ботов"""
#     try:
#         active_bots_data = await api_client.get_active_bots()

#         # Очищаем старые данные
#         old_bots = await cache.get_all_bots()
#         for bot in old_bots:
#             await cache.remove_bot_info(bot.token)

#         # Добавляем новые
#         updated_bots = []
#         for bot_data in active_bots_data:
#             bot_info = BotInfo(**bot_data)
#             await cache.set_bot_info(bot_info)

#             # Обновляем webhook
#             bot = Bot(token=bot_info.token)
#             webhook_url = f"{GATEWAY_BASE_URL}/telegram/bot{bot_info.token}"
#             await bot.set_webhook(webhook_url, drop_pending_updates=True)
#             await bot.session.close()

#             updated_bots.append(bot_info.company_name)

#         return {
#             "status": "success",
#             "updated_bots": updated_bots,
#             "count": len(updated_bots)
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to refresh bots: {str(e)}")