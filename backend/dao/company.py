from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.dao.base import BaseDAO
from backend.enums import CompanyStatusEnum
from backend.models.company import Company
from backend.models.subscription import Subscription as SubscriptionModel
from backend.schemas.company import CompanyCreate, CompanyUpdate


class CompanyDAO(BaseDAO[Company, CompanyCreate, CompanyUpdate]):
    def __init__(self):
        super().__init__(Company)

    async def get_by_inn(self, session: AsyncSession, *, inn: str) -> Optional[Company]:
        result = await session.execute(
            select(self.model).filter(
                self.model.inn == inn, self.model.deleted_at.is_(None)
            )
        )
        return result.scalars().first()

    async def get_by_ogrn(
        self, session: AsyncSession, *, ogrn: str
    ) -> Optional[Company]:
        result = await session.execute(
            select(self.model).filter(
                self.model.ogrn == ogrn, self.model.deleted_at.is_(None)
            )
        )
        return result.scalars().first()

    async def get_company_detailed_by_id(
        self, session: AsyncSession, *, company_id: int
    ) -> Optional[Company]:
        """
        Получает компанию с подробной информацией о ее подписках и кэшбеке.
        Args:
            company_id: ID компании
        Returns:
            Company с загруженными связанными данными или None
        """
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.owner_user_role),
                selectinload(self.model.default_cashback_config),
                selectinload(self.model.subscriptions).options(
                    selectinload(SubscriptionModel.tariff_plan)
                ),
            )
            .filter(self.model.id == company_id)
        )
        result = await session.execute(stmt)
        company_for_response = result.scalars().first()
        return company_for_response

    async def create_company_with_owner(
        self,
        db: AsyncSession,
        *,
        obj_in: CompanyCreate,
        owner_user_role_id: int,
        initial_status: CompanyStatusEnum,
    ) -> Company:
        company_obj = self.model(
            **obj_in.model_dump(exclude={"initial_cashback_percentage"}),
            owner_user_role_id=owner_user_role_id,
            status=initial_status,
        )
        db.add(company_obj)
        await db.flush()
        await db.refresh(company_obj)
        return company_obj
