import logging
import os
import time
from typing import Union

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import DefaultKeyBuilder, Redis, RedisStorage
from aiogram.types import BotCommand
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.config.main_config import Config
from src.core.context import AppContext
from src.handlers import (admin, main_menu, reminder_creation,
                          reminder_management, test_handlers,
                          view_created_reminders)
from src.middlewares.config import ConfigMiddleware
from src.middlewares.data_loader import LoadDataMiddleware
from src.middlewares.database import DBMiddleware
from src.middlewares.redis import RedisMiddleware
from src.services.reminder import ReminderService
from src.services.scheduler import SchedulerService


async def setup_full_app(
    dp: Dispatcher,
    bot: Bot,
    pool: async_sessionmaker[AsyncSession],
    bot_config: Config,
    redis: Redis,
    scheduler: AsyncIOScheduler,
):
    setup_timezone()
    setup_logging()
    setup_global_dependencies(bot)
    setup_services(dp, scheduler)
    setup_middlewares(dp, pool, bot_config, redis)
    setup_handlers(dp)

    await setup_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


async def setup_commands(bot: Bot):
    commands = [
        BotCommand(command="get_all", description="Все пользователи"),
        BotCommand(command="check_state", description="Проверить FSM"),
        BotCommand(command="cancel_check_state", description="Отменить проверку FSM"),
    ]
    await bot.set_my_commands(commands)


def setup_global_dependencies(bot: Bot) -> None:
    AppContext.set_bot(bot)


def setup_timezone():
    os.environ["TZ"] = "Europe/Moscow"
    time.tzset()


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s",
    )
    logger = logging.getLogger(__name__)
    logger.level = logging.INFO


def setup_services(dp: Dispatcher, scheduler: AsyncIOScheduler) -> None:

    scheduler_service = SchedulerService(scheduler=scheduler)
    reminder_service = ReminderService(scheduler_service=SchedulerService)
    dp.workflow_data.update(
        scheduler_service=scheduler_service, reminder_service=reminder_service
    )


def setup_scheduler(config: Config) -> AsyncIOScheduler:

    redis_jobstore_config = {
        "password": config.redis.password,
        "host": config.redis.host,
        "port": config.redis.port,
        "db": config.redis.database,
    }
    jobstores = {"default": RedisJobStore(**redis_jobstore_config)}
    scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="Europe/Moscow")
    scheduler.start()
    return scheduler


def setup_handlers(dp: Dispatcher) -> None:
    dp.include_router(main_menu.router)
    dp.include_router(reminder_creation.router)
    dp.include_router(view_created_reminders.router)
    dp.include_router(admin.router)
    dp.include_router(test_handlers.router)
    dp.include_router(reminder_management.router)


def setup_middlewares(
    dp: Dispatcher,
    pool: async_sessionmaker[AsyncSession],
    bot_config: Config,
    redis: Redis,
) -> None:
    dp.update.outer_middleware(ConfigMiddleware(bot_config))
    dp.update.outer_middleware(DBMiddleware(pool))
    dp.update.outer_middleware(RedisMiddleware(redis))
    dp.update.outer_middleware(LoadDataMiddleware())


def setup_storage(config: Config) -> Union[MemoryStorage, RedisStorage]:

    if config.tg_bot.use_redis:
        storage = RedisStorage.from_url(
            url=config.redis.create_uri(),
            key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True),
        )
    else:
        storage = MemoryStorage()

    return storage
