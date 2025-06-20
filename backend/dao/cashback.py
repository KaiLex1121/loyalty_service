from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.base import BaseDAO
from backend.models.promotions.cashback_config import CashbackConfig
from backend.schemas.cashback import CashbackConfigCreate  # Предполагаем схему


class CashbackConfigDAO(
    BaseDAO[CashbackConfig, CashbackConfigCreate, CashbackConfigCreate]
):
    def __init__(self):
        super().__init__(CashbackConfig)

    async def get_by_company_id(
        self, session: AsyncSession, *, company_id: int
    ) -> Optional[CashbackConfig]:
        """Получает активную конфигурацию кэшбэка для компании."""
        result = await session.execute(
            select(self.model).filter(
                self.model.company_id == company_id,
                self.model.deleted_at.is_(
                    None
                ),  # Учитываем мягкое удаление, если есть в Base
            )
        )
        return result.scalars().first()
