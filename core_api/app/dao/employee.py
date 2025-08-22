from typing import List, Optional

from app.dao.base import BaseDAO
from app.models.account import (
    Account as AccountModel,  # Для join в get_active_by_work_phone
)
from app.models.employee_role import EmployeeRole, employee_role_outlet_association
from app.models.outlet import Outlet
from app.schemas.company_employee import (  # Для типа UpdateSchema в CRUDBase
    EmployeeCreate,
    EmployeeUpdate,
)
from sqlalchemy import delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload


# EmployeeCreateRequest не используется как CreateSchema для CRUDBase, т.к. создание EmployeeRole сложнее
class EmployeeRoleDAO(BaseDAO[EmployeeRole, EmployeeCreate, EmployeeUpdate]):

    def __init__(self):
        super().__init__(EmployeeRole)

    async def create_employee_role(
        self,
        session: AsyncSession,
        *,
        account_id: int,
        company_id: int,
        position: Optional[str],
        work_full_name: Optional[str],
        work_email: Optional[str],
        work_phone_number: Optional[str],
    ) -> EmployeeRole:
        db_obj = self.model(
            account_id=account_id,
            company_id=company_id,
            position=position,
            work_full_name=work_full_name,
            work_email=work_email,
            work_phone_number=work_phone_number,
        )
        session.add(db_obj)
        await session.flush()
        await session.refresh(db_obj)
        return db_obj

    async def get_by_work_phone_and_company_id_with_account(  # Новый метод
        self, session: AsyncSession, work_phone_number: str, company_id: int
    ) -> Optional[EmployeeRole]:
        stmt = (
            select(self.model)
            .options(selectinload(self.model.account))  # Загружаем связанный Account
            .filter(
                self.model.work_phone_number == work_phone_number,
                self.model.company_id == company_id,
                self.model.deleted_at.is_(None),
            )
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_by_account_id_and_company_id(
        self, session: AsyncSession, *, account_id: int, company_id: int
    ) -> Optional[EmployeeRole]:
        result = await session.execute(
            select(self.model).filter(
                self.model.account_id == account_id,
                self.model.company_id == company_id,
                self.model.deleted_at.is_(None),
            )
        )
        return result.scalars().first()

    async def get_by_account_id(
        self, session: AsyncSession, account_id: int
    ) -> Optional[EmployeeRole]:
        """Находит EmployeeRole по account_id."""
        stmt = select(self.model).filter(
            self.model.account_id == account_id, self.model.deleted_at.is_(None)
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_by_id_with_details(
        self,
        session: AsyncSession,
        *,
        employee_role_id: int,
        include_deleted: bool = False,
    ) -> Optional[EmployeeRole]:
        """
        Получает сотрудника по его ID и загружает связанные Account и assigned_outlets.
        """
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.account),
                selectinload(self.model.assigned_outlets),
            )
            .filter(self.model.id == employee_role_id)
        )
        if not include_deleted:
            stmt = stmt.filter(self.model.deleted_at.is_(None))

        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_multi_by_company_id_with_details(
        self, session: AsyncSession, *, company_id: int, skip: int = 0, limit: int = 100
    ) -> List[EmployeeRole]:
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.account),
                selectinload(self.model.assigned_outlets),
            )
            .filter(
                self.model.company_id == company_id, self.model.deleted_at.is_(None)
            )
            .order_by(self.model.id)
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def set_assigned_outlets(
        self,
        session: AsyncSession,
        *,
        employee_role: EmployeeRole,
        outlets_to_assign: List[Outlet],  # <--- Теперь принимает список объектов Outlet
    ):
        """Устанавливает новые торговые точки для сотрудника, заменяя старые."""
        employee_role.assigned_outlets = (
            outlets_to_assign  # SQLAlchemy обработает изменения в M2M
        )
        session.add(
            employee_role
        )  # Добавляем в сессию, чтобы изменения M2M были отслежены
        await session.flush()  # Применяем изменения в ассоциативной таблице
        await session.refresh(
            employee_role, ["assigned_outlets"]
        )  # Обновляем связь в объекте

    async def count_active_by_company_id(
        self, session: AsyncSession, *, company_id: int
    ) -> int:
        # ... (реализация как в предыдущем ответе) ...
        result = await session.execute(
            select(func.count(self.model.id)).filter(
                self.model.company_id == company_id, self.model.deleted_at.is_(None)
            )
        )
        count = result.scalar_one_or_none()
        return count if count is not None else 0

    async def get_active_by_work_phone(
        self,
        session: AsyncSession,
        *,
        work_phone_number: str,
        company_id: Optional[int] = None,
    ) -> Optional[EmployeeRole]:
        # ... (реализация как в предыдущем ответе) ...
        if not work_phone_number:
            return None
        stmt = (
            select(self.model)
            .options(selectinload(self.model.account))
            .join(AccountModel, AccountModel.id == self.model.account_id)
            .filter(
                self.model.work_phone_number == work_phone_number,
                self.model.deleted_at.is_(None),
                AccountModel.is_active == True,
                AccountModel.deleted_at.is_(None),
            )
        )
        if company_id:
            stmt = stmt.filter(self.model.company_id == company_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def find_by_work_phone_and_company_id(
        self, session: AsyncSession, phone_number: str, company_id: int
    ) -> Optional[EmployeeRole]:
        """
        Находит активного сотрудника по рабочему номеру телефона в конкретной компании.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.work_phone_number == phone_number,
                self.model.company_id == company_id,
                self.model.deleted_at.is_(None)
            )
            .options(selectinload(self.model.account)) # Загружаем связанный Account
        )
        result = await session.execute(stmt)
        return result.scalars().first()


    async def get_by_id_with_details_including_deleted(
        self, session: AsyncSession, *, employee_role_id: int
    ) -> Optional[EmployeeRole]:
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.account),
                selectinload(self.model.assigned_outlets),
            )
            .filter(self.model.id == employee_role_id)  # Без фильтра по deleted_at
        )
        result = await session.execute(stmt)
        return result.scalars().first()
