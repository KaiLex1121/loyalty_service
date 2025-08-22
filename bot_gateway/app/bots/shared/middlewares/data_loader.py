from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from app.api_client import CoreApiClient
from app.cache_client import CacheClient


class LoadDataMiddleware(BaseMiddleware):

    def __init__(self, cache_client: CacheClient, api_client: CoreApiClient) -> None:
        self.cache = cache_client
        self.api_client = api_client

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:

        # Получаем токен бота из контекста, который Aiogram предоставляет
        bot = data.get("bot")
        if not bot:
            return await handler(event, data)

        # Используем наш CacheClient для получения информации
        cache = self.cache

        try:
            bot_info = await cache.get_bot_info(bot.token)
            if bot_info:
                data["company_id"] = bot_info.company_id
                data["company_name"] = bot_info.company_name
                data["bot_type"] = bot_info.bot_type
                data["api_client"] = self.api_client
        finally:
            await cache.close()

        # Вызываем следующий middleware или сам хендлер
        return await handler(event, data)
