# backend/dao/promotion.py
import datetime
from typing import Optional, Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from backend.dao.base import BaseDAO
from backend.enums import PromotionStatusEnum, PromotionTypeEnum
from backend.models.promotions.cashback_config import CashbackConfig  # Для joinedload
from backend.models.promotions.promotion import Promotion
from backend.schemas.company_promotion import (  # Вместо PromotionCreateInternal; Нейминг схем
    PromotionCreateInternal,
    PromotionUpdate,
)


class PromotionDAO(BaseDAO[Promotion, PromotionCreateInternal, PromotionUpdate]):
    def __init__(self):
        super().__init__(Promotion)

    async def get_by_id_with_details(
        self, session: AsyncSession, promotion_id: int
    ) -> Optional[Promotion]:
        stmt = (
            select(self.model)
            .where(self.model.id == promotion_id, self.model.deleted_at.is_(None))
            .options(
                joinedload(self.model.cashback_config),
                # selectinload(self.model.usages) # Если usages нужны часто и их много
            )
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_active_promotions_for_company(
        self,
        session: AsyncSession,
        company_id: int,
        current_date: Optional[datetime.datetime] = None,
        promotion_type: Optional[PromotionTypeEnum] = None,
    ) -> Sequence[Promotion]:
        if current_date is None:
            current_date = datetime.datetime.now(datetime.timezone.utc)

        stmt = (
            select(self.model)
            .where(
                self.model.company_id == company_id,
                self.model.status == PromotionStatusEnum.ACTIVE,
                self.model.deleted_at.is_(None),
                self.model.start_date <= current_date,
                or_(self.model.end_date.is_(None), self.model.end_date >= current_date),
            )
            .options(joinedload(self.model.cashback_config))
            .order_by(self.model.priority.desc(), self.model.id)
        )

        if promotion_type:
            stmt = stmt.where(self.model.promotion_type == promotion_type)

        result = await session.execute(stmt)
        return result.scalars().all()

    async def find_by_name_for_company(
        self, session: AsyncSession, name: str, company_id: int
    ) -> Optional[Promotion]:
        stmt = select(self.model).where(
            self.model.company_id == company_id,
            self.model.name == name,
            self.model.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def increment_total_uses(
        self, session: AsyncSession, promotion_id: int, increment_by: int = 1
    ) -> Optional[Promotion]:
        # Получаем объект через get_active, чтобы убедиться, что он не удален
        promotion = await self.get_active(session, id_=promotion_id)
        if promotion:
            promotion.current_total_uses = (
                promotion.current_total_uses or 0
            ) + increment_by
            session.add(
                promotion
            )  # SQLAlchemy отслеживает изменения, но явный add не повредит
            await session.flush()
            await session.refresh(promotion)
            return promotion
        return None

    async def get_promotions_by_company_id(
        self, session: AsyncSession, company_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[Promotion]:
        stmt = (
            select(self.model)
            .where(self.model.company_id == company_id, self.model.deleted_at.is_(None))
            .options(joinedload(self.model.cashback_config))
            .order_by(self.model.created_at.desc())  # Сортировка по дате создания
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def count_by_company_id(self, session: AsyncSession, company_id: int) -> int:
        stmt = select(func.count(self.model.id)).where(
            self.model.company_id == company_id, self.model.deleted_at.is_(None)
        )
        result = await session.execute(stmt)
        return result.scalar_one()
