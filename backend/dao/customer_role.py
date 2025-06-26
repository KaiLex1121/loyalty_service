from typing import Optional, Sequence

from sqlalchemy import and_, select  # Добавил and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload  # Добавил selectinload

from backend.dao.base import BaseDAO
from backend.models.account import Account  # Для joinedload
from backend.models.company import Company  # Для joinedload
from backend.models.customer_role import CustomerRole
from backend.models.subscription import Subscription
from backend.schemas.customer_role import (
    CustomerRoleCreate,
    CustomerRoleCreateInternal,
    CustomerRoleUpdate,
)
from backend.schemas.user_role import UserRoleCreate


class CustomerRoleDAO(BaseDAO[CustomerRole, CustomerRoleCreate, CustomerRoleUpdate]):

    def __init__(self):
        super().__init__(CustomerRole)

    async def find_by_customer_phone_and_company_id_with_details(  # Новый метод
        self, session: AsyncSession, customer_phone_number: str, company_id: int
    ) -> Optional[CustomerRole]:
        # Этот запрос может быть сложным, если делать его одним SQL.
        # Проще в два шага:
        # 1. Найти Account по номеру телефона
        # (Предполагаем, что AccountDAO доступен, например, через HolderDAO,
        # но здесь мы в CustomerRoleDAO, так что это может быть внешний вызов или прямой SQL)

        # Вариант с прямым SQL-запросом с JOIN:
        stmt = (
            select(self.model)  # Select CustomerRole
            .join(Account, self.model.account_id == Account.id)  # Join с Account
            .options(
                selectinload(self.model.account),  # Загрузить детали Account
                selectinload(
                    self.model.company
                ),  # Загрузить детали Company для CustomerRole
            )
            .filter(
                Account.phone_number
                == customer_phone_number,  # Фильтр по номеру телефона клиента
                self.model.company_id == company_id,  # Фильтр по ID компании
                self.model.deleted_at.is_(None),
                Account.deleted_at.is_(None),
            )
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_by_account_id_and_company_id(
        self, session: AsyncSession, account_id: int, company_id: int
    ) -> Optional[CustomerRole]:
        """
        Ищет CustomerRole по account_id и company_id.
        Загружает связанные Account и Company.
        """
        stmt = (
            select(self.model)
            .options(
                joinedload(self.model.account),  # Account - это "один"
                joinedload(self.model.company),  # Company - это "один"
            )
            .filter(
                and_(  # Используем and_ для нескольких условий
                    self.model.account_id == account_id,
                    self.model.company_id == company_id,
                    self.model.deleted_at.is_(None),
                )
            )
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_by_id_with_account_and_company(
        self, session: AsyncSession, customer_role_id: int
    ) -> Optional[CustomerRole]:
        """
        Получает CustomerRole по его ID и загружает связанные Account и Company.
        """
        stmt = (
            select(self.model)
            .options(joinedload(self.model.account), joinedload(self.model.company))
            .filter(self.model.id == customer_role_id, self.model.deleted_at.is_(None))
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_active_by_id_with_account(  # Пример, если нужна загрузка Account
        self, session: AsyncSession, id_: int
    ) -> Optional[CustomerRole]:
        result = await session.execute(
            select(self.model)
            .options(joinedload(self.model.account))  # Загружаем Account
            .filter(self.model.id == id_, self.model.deleted_at.is_(None))
        )
        return result.scalars().first()

    async def get_all_for_account(  # Может понадобиться, чтобы показать клиенту все его профили в разных компаниях
        self, session: AsyncSession, account_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[CustomerRole]:
        stmt = (
            select(self.model)
            .options(
                joinedload(self.model.company)
            )  # Загружаем компанию для каждого CustomerRole
            .filter(
                self.model.account_id == account_id, self.model.deleted_at.is_(None)
            )
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
