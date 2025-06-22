# backend/dao/company_default_cashback_config.py
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.base import BaseDAO
from backend.models.company_default_cashback_config import CompanyDefaultCashbackConfig
from backend.schemas.company_default_cashback_config import (
    CompanyDefaultCashbackConfigCreate,
    CompanyDefaultCashbackConfigUpdate,
)


class CompanyDefaultCashbackConfigDAO(
    BaseDAO[
        CompanyDefaultCashbackConfig,
        CompanyDefaultCashbackConfigCreate,
        CompanyDefaultCashbackConfigUpdate,
    ]
):
    def __init__(self):
        super().__init__(CompanyDefaultCashbackConfig)

    async def get_by_company_id(
        self, session: AsyncSession, company_id: int
    ) -> Optional[CompanyDefaultCashbackConfig]:
        """
        Получает активную конфигурацию базового кэшбэка для компании.
        Если нужна не только активная, можно добавить параметр is_active=None.
        """
        stmt = select(self.model).where(
            self.model.company_id == company_id, self.model.deleted_at.is_(None)
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_active_by_company_id(
        self, session: AsyncSession, company_id: int
    ) -> Optional[CompanyDefaultCashbackConfig]:
        """
        Получает именно активную конфигурацию базового кэшбэка для компании.
        """
        stmt = select(self.model).where(
            self.model.company_id == company_id,
            self.model.is_active == True,  # Явно проверяем флаг активности
            self.model.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        return result.scalars().first()
