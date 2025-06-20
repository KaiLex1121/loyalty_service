from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.dao.base import BaseDAO
from backend.models.tariff_plan import TariffPlan
from backend.schemas.tariff_plan import TariffPlanCreate, TariffPlanUpdate


class TariffPlanDAO(BaseDAO[TariffPlan, TariffPlanCreate, TariffPlanUpdate]):
    def __init__(self):
        super().__init__(TariffPlan)

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[TariffPlan]:
        result = await db.execute(
            select(self.model).filter(
                self.model.name == name, self.model.deleted_at.is_(None)
            )
        )
        return result.scalars().first()

    async def get_by_internal_name(
        self, db: AsyncSession, *, internal_name: str
    ) -> Optional[TariffPlan]:
        result = await db.execute(
            select(self.model).filter(
                self.model.internal_name == internal_name,
                self.model.deleted_at.is_(None),
            )
        )
        return result.scalars().first()
