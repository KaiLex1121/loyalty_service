from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional

from backend.dao.base import BaseDAO
from backend.models.user_role import UserRole
from backend.schemas.user_role import UserRoleCreate # Предполагаем такую схему

class UserRoleDAO(BaseDAO[UserRole, UserRoleCreate, UserRoleCreate]): # UpdateSchema пока та же
    async def get_by_account_id(self, session: AsyncSession, *, account_id: int) -> Optional[UserRole]:
        result = await session.execute(select(self.model).filter(self.model.account_id == account_id))
        return result.scalars().first()

    async def create_for_account(self, session: AsyncSession, *, obj_in: UserRoleCreate, account_id: int) -> UserRole:
        db_obj = self.model(**obj_in.model_dump(), account_id=account_id)
        session.add(db_obj)
        await session.flush()
        await session.refresh(db_obj)
        return db_obj
