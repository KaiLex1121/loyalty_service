from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.dao.base import BaseDAO
from backend.models.account import Account
from backend.models.employee_role import EmployeeRole
from backend.models.user_role import UserRole
from backend.schemas.account import AccountCreate, AccountUpdate


class AccountDAO(BaseDAO[Account, AccountCreate, AccountUpdate]):
    def __init__(self):
        super().__init__(Account)

    async def get_by_id_without_relations(
        self, session: AsyncSession, *, id_: int
    ) -> Optional[Account]:
        statement = select(self.model).where(
            and_(self.model.id == id_, self.model.deleted_at.is_(None))
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_id_with_profiles(
        self, db: AsyncSession, *, id_: int
    ) -> Optional[Account]:
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.user_profile).selectinload(
                    UserRole.companies_owned
                ),
                selectinload(self.model.employee_profile).selectinload(
                    EmployeeRole.company
                ),
                selectinload(self.model.customer_profile),
            )
            .filter(Account.id == id_)
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_by_phone_number_without_relations(
        self, session: AsyncSession, *, phone_number: str
    ) -> Optional[Account]:
        statement = select(self.model).where(
            and_(
                self.model.phone_number == phone_number, self.model.deleted_at.is_(None)
            )
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_phone_number_with_profiles(
        self, session: AsyncSession, *, phone_number: str
    ):
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.user_profile),
                selectinload(self.model.employee_profile),
                selectinload(self.model.customer_profile),
            )
            .filter(Account.phone_number == phone_number)
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def mark_as_active(self, session: AsyncSession, *, account: Account) -> None:
        account.is_active = True
        session.add(account)
        return account

    async def create(self, session: AsyncSession, *, obj_in: AccountCreate) -> Account:
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        session.add(db_obj)
        await session.flush()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self, session: AsyncSession, *, db_ojb: Account, obj_in: AccountUpdate | dict
    ) -> Account:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_ojb, field, value)
        session.add(db_ojb)
        return db_ojb
