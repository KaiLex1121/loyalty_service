from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar(
    "CreateSchemaType", bound=BaseModel
)  # Ограничение: должна быть Pydantic модель
UpdateSchemaType = TypeVar(
    "UpdateSchemaType", bound=BaseModel
)  # Ограничение: должна быть Pydantic модель


class BaseDAO(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def create(
        self, session: AsyncSession, *, obj_in: CreateSchemaType
    ) -> ModelType:
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        session.add(db_obj)
        await session.flush()  # Для получения ID и проверки ограничений до коммита
        await session.refresh(db_obj)  # Для обновления server_default и т.д.
        return db_obj

    async def update(
        self,
        session: AsyncSession,
        *,
        db_obj: ModelType,  # Существующий объект SQLAlchemy из БД
        obj_in: Union[
            UpdateSchemaType, Dict[str, Any]
        ],  # Схема Pydantic с обновлениями или словарь
    ) -> ModelType:
        if hasattr(db_obj, "is_deleted") and db_obj.is_deleted:
            pass
        obj_data = db_obj.as_dict()

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(
                exclude_unset=True
            )  # exclude_unset=True чтобы обновлять только переданные поля
        for field, value in update_data.items():
            if field in update_data:
                setattr(db_obj, field, value)
        session.add(
            db_obj
        )  # Добавляем измененный объект обратно в сессию (хотя он уже там)
        await session.flush()
        await session.refresh(db_obj)
        return db_obj

    async def get(self, session, id_: int) -> ModelType:
        result = await session.execute(select(self.model).where(self.model.id == id_))
        return result.scalar_one()

    async def get_active(self, db: AsyncSession, id_: Any) -> Optional[ModelType]:
        result = await db.execute(
            select(self.model).filter(
                self.model.id == id_, self.model.deleted_at.is_(None)
            )
        )
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        stmt = select(self.model)
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_multi_active(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Получает список активных (не мягко удаленных) записей."""
        return await self.get_multi(db, skip=skip, limit=limit)

    async def soft_delete(self, db: AsyncSession, *, id_: Any) -> Optional[ModelType]:
        db_obj = await self.get_active(
            db, id_=id_
        )  # Ищем только активный объект для удаления
        if not db_obj:
            return None

        db_obj.deleted_at = datetime.now(timezone.utc)
        db.add(db_obj)
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
        await db.refresh(db_obj)
        return db_obj

    async def hard_delete(self, db: AsyncSession, *, id_: Any) -> Optional[ModelType]:
        db_obj = await self.get(
            db, id_=id_
        )  # Получаем объект, неважно, удален он мягко или нет
        if db_obj:
            await db.delete(db_obj)
        return db_obj

    async def count(self, session: AsyncSession) -> int:
        result = await session.execute(select(func.count(self.model.id)))
        return result.scalar_one()

    def add(self, obj: ModelType, session: AsyncSession) -> None:
        session.add(obj)

    async def commit(self, session: AsyncSession) -> None:
        await session.commit()

    async def flush(self, *objects, session: AsyncSession) -> None:
        await session.flush(objects)

    async def refresh(self, obj: ModelType, session: AsyncSession) -> None:
        await session.refresh(obj)
