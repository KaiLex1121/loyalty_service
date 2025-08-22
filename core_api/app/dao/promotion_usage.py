# backend/dao/promotion_usage.py
from typing import Optional, Sequence

from app.dao.base import BaseDAO
from app.models.promotions.promotion_usage import PromotionUsage
from app.schemas.promotion_usage import (  # Нейминг схем
    PromotionUsageCreate,
    PromotionUsageUpdate,
)
from pydantic import BaseModel  # Для заглушки Update схемы
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class PromotionUsageDAO(
    BaseDAO[
        PromotionUsage,
        PromotionUsageCreate,  # Используем BlaCreate
        PromotionUsageUpdate,
    ]
):
    def __init__(self):
        super().__init__(PromotionUsage)

    async def get_usages_for_promotion(
        self, session: AsyncSession, promotion_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[PromotionUsage]:
        stmt = (
            select(self.model)
            .where(
                self.model.promotion_id == promotion_id, self.model.deleted_at.is_(None)
            )
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_usages_by_customer_for_promotion(
        self, session: AsyncSession, promotion_id: int, customer_role_id: int
    ) -> Sequence[PromotionUsage]:
        stmt = (
            select(self.model)
            .where(
                self.model.promotion_id == promotion_id,
                self.model.customer_role_id == customer_role_id,
                self.model.deleted_at.is_(None),
            )
            .order_by(self.model.created_at.desc())
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def count_usages_by_customer_for_promotion(
        self, session: AsyncSession, promotion_id: int, customer_role_id: int
    ) -> int:
        stmt = select(func.count(self.model.id)).where(
            self.model.promotion_id == promotion_id,
            self.model.customer_role_id == customer_role_id,
            self.model.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        return result.scalar_one()

    async def get_by_transaction_id(
        self, session: AsyncSession, transaction_id: int
    ) -> Optional[PromotionUsage]:
        stmt = select(self.model).where(
            self.model.transaction_id == transaction_id, self.model.deleted_at.is_(None)
        )
        result = await session.execute(stmt)
        return result.scalars().first()
