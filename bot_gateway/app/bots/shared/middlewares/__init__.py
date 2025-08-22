from aiogram import Dispatcher
from app.bots.shared.middlewares.data_loader import LoadDataMiddleware
from app.cache_client import CacheClient
from app.api_client import CoreApiClient
# from app.bots.shared.middlewares.employee_auth import AuthMiddleware

def setup_shared_middlewares(dp: Dispatcher, cache_client: CacheClient, api_client: CoreApiClient):
    dp.update.middleware(LoadDataMiddleware(cache_client=cache_client, api_client=api_client))
    # dp.update.middleware(AuthMiddleware())