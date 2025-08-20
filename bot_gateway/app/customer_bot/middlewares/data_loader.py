from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from app.cache import CacheClient


class LoadDataMiddleware(BaseMiddleware):

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
        cache = CacheClient()
        try:
            bot_info = await cache.get_bot_info(bot.token)
            if bot_info:
                # Добавляем данные в "контейнер"
                data["company_id"] = bot_info.company_id
                data["company_name"] = bot_info.company_name
        finally:
            await cache.close()

        # Вызываем следующий middleware или сам хендлер
        return await handler(event, data)
