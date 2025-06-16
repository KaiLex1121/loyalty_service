from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.dao.base import BaseDAO
from backend.models.company import Company
from backend.models.subscription import Subscription
from backend.models.user_role import UserRole
from backend.schemas.user_role import UserRoleCreate


class UserRoleDAO(BaseDAO[UserRole, UserRoleCreate, UserRoleCreate]):
    def __init__(self):
        super().__init__(UserRole)

    async def get_by_account_id(
        self, session: AsyncSession, *, account_id: int
    ) -> Optional[UserRole]:
        result = await session.execute(
            select(self.model).filter(self.model.account_id == account_id)
        )
        return result.scalars().first()

    async def create_for_account(
        self, session: AsyncSession, *, obj_in: UserRoleCreate
    ) -> UserRole:
        db_obj = await self.create(session, obj_in=obj_in)
        return db_obj

    async def get_user_role_companies_detailed(
        self, user_role_id: int, session: AsyncSession
    ) -> Optional[UserRole]:
        """
        Получает роль пользователя с подробной информацией о принадлежащих компаниях,
        включая настройки кэшбека и подписки с тарифными планами.
        Args:
            user_role_id: ID роли пользователя
        Returns:
            UserRole с загруженными связанными данными или None
        """
        stmt = (
            select(UserRole)
            .options(
                selectinload(UserRole.companies_owned).options(
                    selectinload(Company.cashback),
                    selectinload(Company.subscriptions).options(
                        selectinload(Subscription.tariff_plan)
                    ),
                )
            )
            .filter(UserRole.id == user_role_id)
        )

        result = await session.execute(stmt)
        return result.scalars().first()
