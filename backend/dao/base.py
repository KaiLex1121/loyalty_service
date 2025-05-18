from typing import Generic, List, Type, TypeVar

from sqlalchemy import delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.db.base import Base

Model = TypeVar("Model", Base, Base)


class BaseDAO(Generic[Model]):
    def __init__(self, model: Type[Model]):
        self.model = model

    async def get_all(self, session) -> List[Model]:
        result = await session.execute(select(self.model))
        return result.all()

    async def get_by_id(self, session, id_: int) -> Model:
        result = await session.execute(select(self.model).where(self.model.id == id_))
        return result.scalar_one()

    async def delete_all(self):
        await self.session.execute(delete(self.model))

    async def count(self):
        result = await self.session.execute(select(func.count(self.model.id)))
        return result.scalar_one()

    def add(self, obj: Model):
        self.session.add(obj)

    async def commit(self):
        await self.session.commit()

    async def flush(self, *objects):
        await self.session.flush(objects)

    async def refresh(self, obj: Model):
        await self.session.refresh(obj)
