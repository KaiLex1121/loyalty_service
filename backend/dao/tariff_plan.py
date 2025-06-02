from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.dao.base import BaseDAO
from backend.enums.back_office import TariffStatusEnum
from backend.models.tariff_plan import TariffPlan

# Схемы для TariffPlan (Create, Update) могут понадобиться для админки тарифов


class TariffPlanDAO(BaseDAO[TariffPlan, TariffPlan, TariffPlan]):
    def __init__(self):
        super().__init__(TariffPlan)

    async def get_trial_plan(self, db: AsyncSession) -> Optional[TariffPlan]:
        result = await db.execute(
            select(self.model)
            .filter(
                self.model.is_trial == True,
                self.model.status == TariffStatusEnum.ACTIVE,
            )
            .order_by(self.model.created_at.desc())
        )
        return result.scalars().first()

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[TariffPlan]:
        result = await db.execute(
            select(self.model).filter(
                self.model.name == name, self.model.deleted_at.is_(None)
            )
        )
        return result.scalars().first()
