import select
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.base import BaseDAO
from backend.models.user import User
from backend.schemas.user import UserCreate, UserUpdate

class UserDAO(BaseDAO[User]):
    def __init__(self):
        super().__init__(User)

    async def get_by_phone_number(self, db: AsyncSession, *, phone_number: str) -> Optional[User]:
        statement = select(User).where(User.phone_number == phone_number)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get(self, db: AsyncSession, *, user_id: int) -> Optional[User]:
        statement = select(User).where(User.id == user_id)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        db_obj = User(
            phone_number=obj_in.phone_number,
            email=obj_in.email,
            is_active=obj_in.is_active,
        )
        db.add(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: User, obj_in: UserUpdate | dict
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        return db_obj
