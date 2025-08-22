from typing import List, Optional

from app.dao.base import BaseDAO
from app.enums import (  # Прямой импорт, если не через __init__
    TariffStatusEnum,
)
from app.models.tariff_plan import TariffPlan
from app.schemas.company_tariff_plan import (  # Используем наши схемы
    TariffPlanCreate,
    TariffPlanUpdate,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


class TariffPlanDAO(BaseDAO[TariffPlan, TariffPlanCreate, TariffPlanUpdate]):
    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[TariffPlan]:
        """Получает тарифный план по имени."""
        result = await db.execute(
            select(self.model).filter(
                self.model.name == name, self.model.deleted_at.is_(None)
            )
        )
        return result.scalars().first()

    async def get_all_active_public_plans(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[TariffPlan]:
        """Получает все активные и публичные тарифные планы."""
        stmt = (
            select(self.model)
            .filter(
                self.model.status == TariffStatusEnum.ACTIVE,
                self.model.is_public == True,
                self.model.deleted_at.is_(None),
            )
            .order_by(self.model.sort_order)  # Сортировка
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


tariff_plan_dao = TariffPlanDAO(TariffPlan)
