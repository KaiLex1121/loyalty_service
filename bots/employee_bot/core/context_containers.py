from typing import Optional

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler


class AppContext:
    """Простой контейнер для хранения общих ресурсов приложения."""

    _bot: Optional[Bot] = None
    _scheduler: Optional[AsyncIOScheduler] = None
    # Можно добавить другие ресурсы: db_pool, etc.

    @classmethod
    def set_bot(cls, bot_instance: Bot):

        logger.info("Bot instance set in AppContext.")
        cls._bot = bot_instance

    @classmethod
    def get_bot(cls) -> Bot:
        if cls._bot is None:
            logger.critical("Attempted to get Bot instance before it was set.")
            raise RuntimeError("AppContext: Bot instance has not been initialized.")
        return cls._bot

    @classmethod
    def set_scheduler(cls, scheduler_instance: AsyncIOScheduler):
        logger.info("Scheduler instance set in AppContext.")
        cls._scheduler = scheduler_instance

    @classmethod
    def get_scheduler(cls) -> AsyncIOScheduler:
        if cls._scheduler is None:
            logger.critical("Attempted to get Scheduler instance before it was set.")
            raise RuntimeError(
                "AppContext: Scheduler instance has not been initialized."
            )
        return cls._scheduler
