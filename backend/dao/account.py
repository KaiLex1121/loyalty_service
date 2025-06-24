from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.dao.base import BaseDAO
from backend.models.account import Account
from backend.models.customer_role import CustomerRole
from backend.models.employee_role import EmployeeRole
from backend.models.user_role import UserRole
from backend.schemas.account import AccountCreate, AccountCreateInternal, AccountUpdate


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

    async def get_by_id_with_all_profiles(  # Метод, который у вас уже был, но убедимся, что он грузит customer_roles
        self, session: AsyncSession, id_: int
    ) -> Optional[Account]:
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.user_profile).selectinload(
                    UserRole.companies_owned
                ),  # Для админа
                selectinload(self.model.employee_profile).selectinload(
                    EmployeeRole.company
                ),  # Для сотрудника
                selectinload(self.model.customer_profiles).selectinload(
                    CustomerRole.company
                ),  # Для клиента, все его роли в разных компаниях
            )
            .filter(
                Account.id == id_, Account.deleted_at.is_(None)
            )  # Добавил deleted_at
        )
        result = await session.execute(stmt)
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

    async def get_by_phone_number_with_all_profiles(
        self, session: AsyncSession, *, phone_number: str
    ):
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.user_profile),
                selectinload(self.model.employee_profile),
                selectinload(self.model.customer_profiles).selectinload(
                    CustomerRole.company
                ),
            )
            .filter(Account.phone_number == phone_number)
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def mark_as_active(
        self, session: AsyncSession, *, account: Account
    ) -> Account:
        account.is_active = True
        session.add(account)
        return account

    async def get_by_telegram_id_with_all_profiles(
        self, session: AsyncSession, telegram_user_id: int
    ) -> Optional[Account]:
        """Ищет аккаунт по telegram_user_id и загружает связанные профили."""
        if (
            telegram_user_id is None
        ):  # Проверка на случай, если telegram_user_id не передан
            return None

        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.user_profile),
                selectinload(self.model.employee_profile),
                selectinload(self.model.customer_profiles).selectinload(
                    CustomerRole.company
                ),
            )
            .filter(
                self.model.telegram_user_id == telegram_user_id,
                self.model.deleted_at.is_(None),
            )
        )
        result = await session.execute(stmt)
        return result.scalars().first()
