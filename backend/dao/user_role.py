from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.dao.base import BaseDAO
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
