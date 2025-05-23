from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.base import BaseDAO
from backend.models.account import Account
from backend.schemas.account import AccountCreate, AccountUpdate


class AccountDAO(BaseDAO[Account]):
    def __init__(self):
        super().__init__(Account)

    async def get_by_phone_number(
        self, db: AsyncSession, *, phone_number: str
    ) -> Optional[Account]:
        statement = select(Account).where(Account.phone_number == phone_number)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get(self, db: AsyncSession, *, Account_id: int) -> Optional[Account]:
        statement = select(Account).where(Account.id == Account_id)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: AccountCreate) -> Account:
        db_obj = Account(
            phone_number=obj_in.phone_number,
            email=obj_in.email,
            is_active=obj_in.is_active,
        )
        db.add(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: Account, obj_in: AccountUpdate | dict
    ) -> Account:
        print(obj_in)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        return db_obj
