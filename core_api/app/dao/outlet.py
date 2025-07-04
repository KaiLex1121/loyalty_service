from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.base import BaseDAO
from app.enums import OutletStatusEnum
from app.models.outlet import Outlet
from app.schemas.company_outlet import OutletCreate, OutletUpdate


class OutletDAO(BaseDAO[Outlet, OutletCreate, OutletUpdate]):
    def __init__(self):
        super().__init__(Outlet)

    async def create_with_company(
        self,
        session: AsyncSession,
        *,
        obj_in: OutletCreate,
        company_id: int,
        initial_status: OutletStatusEnum,
    ) -> Outlet:
        """Создает торговую точку с привязкой к ID компании и начальным статусом."""
        # obj_in_data = obj_in.model_dump() # OutletCreateRequest не содержит company_id и status
        db_obj = self.model(
            **obj_in.model_dump(),  # name, address из схемы
            company_id=company_id,
            status=initial_status,
        )
        session.add(db_obj)
        await session.flush()
        await session.refresh(db_obj)
        return db_obj

    async def get_multi_by_company_id(
        self, session: AsyncSession, *, company_id: int, skip: int = 0, limit: int = 100
    ) -> List[Outlet]:
        """Получает список активных торговых точек для указанной компании."""
        stmt = (
            select(self.model)
            .filter(
                self.model.company_id == company_id,
                self.model.deleted_at.is_(None),  # Только не мягко удаленные
            )
            .order_by(self.model.name)  # Сортировка по имени для консистентности
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_outlets_by_ids_and_company_id(
        self, session: AsyncSession, outlet_ids: List[int], company_id: int
    ) -> List[Outlet]:
        """
        Получить активные торговые точки по списку ID для определенной компании.

        Args:
            session: Асинхронная сессия базы данных
            outlet_ids: Список ID торговых точек
            company_id: ID компании

        Returns:
            Список найденных торговых точек
        """
        stmt = select(Outlet).filter(
            Outlet.id.in_(outlet_ids),  # Ищем по списку ID
            Outlet.company_id == company_id,  # Принадлежат нужной компании
            Outlet.deleted_at.is_(None),  # Не удалены
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_by_id_and_company_id(
        self, session: AsyncSession, *, outlet_id: int, company_id: int
    ) -> Optional[Outlet]:
        """Получает активную торговую точку по ее ID и ID компании."""
        result = await session.execute(
            select(self.model).filter(
                self.model.id == outlet_id,
                self.model.company_id == company_id,
                self.model.deleted_at.is_(None),
            )
        )
        return result.scalars().first()

    async def get_by_name_and_company_id(  # Если имя ТТ должно быть уникально в рамках компании
        self, session: AsyncSession, *, name: str, company_id: int
    ) -> Optional[Outlet]:
        result = await session.execute(
            select(self.model).filter(
                self.model.name == name,
                self.model.company_id == company_id,
                self.model.deleted_at.is_(None),
            )
        )
        return result.scalars().first()

    async def count_active_by_company_id(
        self, session: AsyncSession, *, company_id: int
    ) -> int:
        """Подсчитывает количество активных (не мягко удаленных) торговых точек для компании."""
        result = await session.execute(
            select(
                func.count(self.model.id)
            ).filter(  # Используем func.count(self.model.id)
                self.model.company_id == company_id, self.model.deleted_at.is_(None)
            )
        )
        count = (
            result.scalar_one_or_none()
        )  # scalar_one_or_none вернет None, если результат пуст (хотя count всегда вернет число)
        return count if count is not None else 0
