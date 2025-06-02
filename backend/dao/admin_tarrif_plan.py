from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.dao.base import CRUDBase
from backend.enums import \
    TariffStatusEnum  # Прямой импорт, если не через __init__
from backend.models.tariff_plan import TariffPlan
from backend.schemas.tariff_plan import (  # Используем наши схемы
    TariffPlanCreate, TariffPlanUpdate)


class TariffPlanDAO(CRUDBase[TariffPlan, TariffPlanCreate, TariffPlanUpdate]):
    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[TariffPlan]:
        """Получает тарифный план по имени."""
        result = await db.execute(
            select(self.model).filter(
                self.model.name == name, self.model.deleted_at.is_(None)
            )
        )
        return result.scalars().first()

    async def get_trial_plan(self, db: AsyncSession) -> Optional[TariffPlan]:
        """
        Получает текущий активный триальный тарифный план.
        Предполагается, что активный триальный тариф может быть только один.
        """
        stmt = (
            select(self.model)
            .filter(
                self.model.is_trial == True,
                self.model.status == TariffStatusEnum.ACTIVE,  # Только активные триалы
                self.model.deleted_at.is_(None),
            )
            .order_by(
                self.model.created_at.desc()
            )  # Берем самый новый, если их несколько (хотя не должно быть)
        )
        result = await db.execute(stmt)
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
            .order_by(self.model.sort_order, self.model.price)  # Сортировка
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()


tariff_plan_dao = TariffPlanDAO(TariffPlan)
