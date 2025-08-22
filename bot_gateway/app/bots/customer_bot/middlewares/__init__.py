from aiogram import Dispatcher
from app.bots.customer_bot.middlewares.data_loader import LoadDataMiddleware
from app.cache_client import CacheClient
from app.api_client import CoreApiClient

def setup_customer_bot_middlewares(dp: Dispatcher, cache_client: CacheClient, api_client: CoreApiClient):
    dp.update.middleware(LoadDataMiddleware(cache_client=cache_client, api_client=api_client))
