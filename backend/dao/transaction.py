# backend/dao/transaction.py
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from backend.dao.base import BaseDAO
from backend.models.promotions.promotion import Promotion  # Для joinedload
from backend.models.promotions.promotion_usage import PromotionUsage  # Для joinedload
from backend.models.transaction import Transaction
from backend.schemas.transaction import (
    TransactionCreateInternal,  # Вместо TransactionCreateInternal
)
from backend.schemas.transaction import (  # Нейминг схем
    TransactionUpdate,
)


class TransactionDAO(
    BaseDAO[
        Transaction,
        TransactionCreateInternal,  # Используем TransactionCreateInternal
        TransactionUpdate,
    ]
):
    def __init__(self):
        super().__init__(Transaction)

    async def get_transactions_by_customer_id(
        self,
        session: AsyncSession,
        customer_role_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Transaction]:
        stmt = (
            select(self.model)
            .where(
                self.model.customer_role_id == customer_role_id,
                self.model.deleted_at.is_(None),
            )
            .options(
                joinedload(self.model.promotion_usage_entry)
                .joinedload(PromotionUsage.promotion)
                .joinedload(Promotion.cashback_config)
            )
            .order_by(self.model.transaction_time.desc(), self.model.id.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def count_transactions_by_customer_id(
        self, session: AsyncSession, customer_role_id: int
    ) -> int:
        stmt = select(func.count(self.model.id)).where(
            self.model.customer_role_id == customer_role_id,
            self.model.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        return result.scalar_one()

    async def get_by_id_with_details(
        self, session: AsyncSession, id_: int
    ) -> Optional[Transaction]:
        stmt = (
            select(self.model)
            .where(self.model.id == id_, self.model.deleted_at.is_(None))
            .options(
                joinedload(self.model.promotion_usage_entry)
                .joinedload(PromotionUsage.promotion)
                .joinedload(Promotion.cashback_config)
                # Если нужны еще связи для Transaction (Company, CustomerRole, Outlet):
                # joinedload(self.model.company),
                # joinedload(self.model.customer_role),
                # joinedload(self.model.outlet),
            )
        )
        result = await session.execute(stmt)
        return result.scalars().first()
