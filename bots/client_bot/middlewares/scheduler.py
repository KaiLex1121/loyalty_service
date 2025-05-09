from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from apscheduler.schedulers.asyncio import AsyncIOScheduler


class SchedulerMiddleware(BaseMiddleware):
    def __init__(self, scheduler_service: AsyncIOScheduler):
        super().__init__()
        self._scheduler_service = scheduler_service

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Передаем экземпляр шедулера в данные события (data),
        # откуда он будет доступен в хэндлерах по ключу 'scheduler'
        data["scheduler"] = self._scheduler_service
        return await handler(event, data)
