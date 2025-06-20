from sqlalchemy import select
from backend.dao.base import BaseDAO
from backend.models.cashback import Cashback
from backend.schemas.cashback import CashbackConfigCreate  # Предполагаем схему
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

class CashbackConfigDAO(BaseDAO[Cashback, CashbackConfigCreate, CashbackConfigCreate]):
    def __init__(self):
        super().__init__(Cashback)

    async def get_by_company_id(self, session: AsyncSession, *, company_id: int) -> Optional[Cashback]:
        """Получает активную конфигурацию кэшбэка для компании."""
        result = await session.execute(
            select(self.model).filter(
                self.model.company_id == company_id,
                self.model.deleted_at.is_(None) # Учитываем мягкое удаление, если есть в Base
            )
        )
        return result.scalars().first()