from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.dao.base import BaseDAO
from backend.enums.back_office import CompanyStatusEnum
from backend.models.company import Company  # Импорт модели
from backend.models.company import Company as CompanyModel
from backend.schemas.company import (CompanyCreateRequest,  # Схемы Pydantic
                                     CompanyUpdateRequest)


class OtpCodeDAO(BaseDAO[Company], CompanyCreateRequest, CompanyUpdateRequest):
    def __init__(self):
        super().__init__(Company)

    async def get_by_inn(self, db: AsyncSession, *, inn: str) -> Optional[CompanyModel]:
        result = await db.execute(
            select(self.model).filter(
                self.model.inn == inn, self.model.deleted_at.is_(None)
            )
        )
        return result.scalars().first()

    async def create_company_with_owner(
        self,
        db: AsyncSession,
        *,
        obj_in: CompanyCreateRequest,
        owner_user_role_id: int,
        initial_status: CompanyStatusEnum
    ) -> CompanyModel:
        # obj_in_data = obj_in.model_dump() # Уже есть в CRUDBase.create
        # db_obj = self.model(**obj_in_data, owner_user_role_id=owner_user_role_id, status=initial_status)
        # db.add(db_obj)
        # # Коммит и refresh будут в CRUDBase.create или в сервисе
        # return db_obj

        # Если CRUDBase.create принимает только obj_in, то создаем объект здесь
        company_obj = self.model(
            **obj_in.model_dump(),
            owner_user_role_id=owner_user_role_id,
            status=initial_status
        )
        db.add(company_obj)
        await db.flush()  # Чтобы получить ID и другие значения по умолчанию из БД до коммита
        await db.refresh(company_obj)
        return company_obj
