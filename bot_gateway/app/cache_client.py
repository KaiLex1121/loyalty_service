import json
from typing import Optional

import redis.asyncio as redis
from app.core.settings import settings

from shared.schemas.schemas import BotInfo


class CacheClient:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS.REDIS_URI)

    async def get_bot_info(self, token: str) -> Optional[BotInfo]:
        """Получает информацию о боте из кэша."""
        data = await self.redis.get(f"bot_info:{token}")
        if data:
            return BotInfo.model_validate(json.loads(data))
        return None

    async def set_bot_info(self, bot_info: BotInfo):
        """Сохраняет информацию о боте в кэш с TTL."""
        key = f"bot_info:{bot_info.token}"
        await self.redis.set(key, bot_info.model_dump_json())

    async def set_idempotency_key(self, key: str, ttl_seconds: int = 86400) -> bool:
        """
        Устанавливает ключ идемпотентности.
        Возвращает True, если ключ был установлен (первая обработка),
        и False, если ключ уже существовал.
        """
        # SET key value NX EX seconds
        # NX -- Only set the key if it does not already exist.
        return await self.redis.set(key, "processed", ex=ttl_seconds, nx=True)

    async def close(self):
        await self.redis.close()
