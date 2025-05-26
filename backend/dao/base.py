from datetime import datetime, timezone
from typing import Any, Generic, List, Optional, Type, TypeVar

from sqlalchemy import delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseDAO(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, session, id_: int) -> ModelType:
        result = await session.execute(select(self.model).where(self.model.id == id_))
        return result.scalar_one()

    async def get_active(self, db: AsyncSession, id_: Any) -> Optional[ModelType]:
        result = await db.execute(
            select(self.model).filter(
                self.model.id_ == id_, self.model.deleted_at.is_(None)
            )
        )
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        stmt = select(self.model)
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_multi_active(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Получает список активных (не мягко удаленных) записей."""
        return await self.get_multi(db, skip=skip, limit=limit, include_deleted=False)

    async def soft_delete(self, db: AsyncSession, *, id_: Any) -> Optional[ModelType]:
        db_obj = await self.get_active(
            db, id_=id_
        )  # Ищем только активный объект для удаления
        if not db_obj:
            return None

        db_obj.deleted_at = datetime.now(timezone.utc)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # --- Восстановление мягко удаленной записи ---
    async def undelete(self, db: AsyncSession, *, id_: Any) -> Optional[ModelType]:
        """
        Восстанавливает мягко удаленную запись по id_, устанавливая deleted_at = None.
        Возвращает восстановленный объект или None, если объект не найден или не был удален.
        """
        # Ищем запись, включая удаленные, чтобы ее можно было восстановить
        db_obj = await self.get(db, id_=id_)
        if not db_obj:
            return None

        if not db_obj.is_deleted:
            return db_obj

        db_obj.deleted_at = None
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def hard_delete(self, db: AsyncSession, *, id_: Any) -> Optional[ModelType]:
        db_obj = await self.get(
            db, id_=id_
        )  # Получаем объект, неважно, удален он мягко или нет
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj

    async def count(self) -> int:
        result = await self.session.execute(select(func.count(self.model.id_)))
        return result.scalar_one()

    def add(self, obj: ModelType) -> None:
        self.session.add(obj)

    async def commit(self) -> None:
        await self.session.commit()

    async def flush(self, *objects) -> None:
        await self.session.flush(objects)

    async def refresh(self, obj: ModelType) -> None:
        await self.session.refresh(obj)
