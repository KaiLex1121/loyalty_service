from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.database.dao.holder import HolderDAO


class DBMiddleware(BaseMiddleware):
    def __init__(self, pool: async_sessionmaker[AsyncSession]):
        self.pool = pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with self.pool() as session:
            holder_dao = HolderDAO(session)
            data["dao"] = holder_dao
            result = await handler(event, data)
            del data["dao"]
            return result
