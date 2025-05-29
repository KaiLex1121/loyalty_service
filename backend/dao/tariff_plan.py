from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional

from backend.dao.base import BaseDAO
from backend.enums.back_office import TariffStatusEnum
from backend.models.tariff_plan import TariffPlan
# Схемы для TariffPlan (Create, Update) могут понадобиться для админки тарифов

class TariffPlanDAO(BaseDAO[TariffPlan, TariffPlan, TariffPlan]):

    async def get_trial_plan(self, db: AsyncSession) -> Optional[TariffPlan]:
        result = await db.execute(
            select(self.model).filter(self.model.is_trial == True, self.model.status == TariffStatusEnum.ACTIVE).order_by(self.model.created_at.desc())
        )
        return result.scalars().first()
