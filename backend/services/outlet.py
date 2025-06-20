# backend/services/outlet_service.py
from typing import List, Optional

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload  # Для загрузки связей, если нужно для ответа

from backend.core.logger import get_logger
from backend.dao.holder import HolderDAO
from backend.enums import OutletStatusEnum
from backend.exceptions.common import InternalServerError
from backend.exceptions.services.outlet import (
    OutletLimitExceededException,
    OutletNameConflictInCompanyException,
    OutletNotFoundException,
)
from backend.models.company import Company as CompanyModel  # Для проверки лимитов
from backend.models.outlet import Outlet as OutletModel
from backend.schemas.outlet import OutletCreate, OutletResponse, OutletUpdate
from backend.utils.subscription_utils import get_current_subscription

logger = get_logger(__name__)


class OutletService:

    def __init__(self, dao: HolderDAO):
        self.dao = dao

    async def _load_outlet_for_response(
        self, session: AsyncSession, outlet_id: int
    ) -> Optional[OutletModel]:
        return await self.dao.outlet.get_active(session, id_=outlet_id)

    async def create_outlet(
        self,
        session: AsyncSession,
        company: CompanyModel,  # Компания, к которой привязываем, уже проверена на доступ
        outlet_data: OutletCreate,
    ) -> OutletResponse:
        # 1. Проверка на уникальность имени в рамках компании
        existing_outlet_by_name = await self.dao.outlet.get_by_name_and_company_id(
            session, name=outlet_data.name, company_id=company.id
        )
        if existing_outlet_by_name:
            raise OutletNameConflictInCompanyException(
                name=outlet_data.name, company_id=company.id
            )

        # 2. Проверка лимитов на количество торговых точек
        current_subscription = get_current_subscription(company)
        if current_subscription and current_subscription.tariff_plan:
            max_outlets = current_subscription.tariff_plan.max_outlets
            if max_outlets is not None and max_outlets > 0:  # 0 или None - безлимит
                current_outlet_count = await self.dao.outlet.count_active_by_company_id(
                    session, company_id=company.id
                )
                if current_outlet_count >= max_outlets:
                    raise OutletLimitExceededException(
                        company_id=company.id, limit=max_outlets
                    )

        new_outlet_model = await self.dao.outlet.create_with_company(
            session,
            obj_in=outlet_data,
            company_id=company.id,
            initial_status=OutletStatusEnum.OPEN,
        )

        return OutletResponse.model_validate(new_outlet_model)

    async def get_outlets_for_company(
        self, session: AsyncSession, company_id: int, skip: int, limit: int
    ) -> List[OutletResponse]:
        # Права на company_id должны быть проверены до вызова этого метода (например, в эндпоинте через get_owned_company)
        outlet_models = await self.dao.outlet.get_multi_by_company_id(
            session, company_id=company_id, skip=skip, limit=limit
        )
        return [OutletResponse.model_validate(outlet) for outlet in outlet_models]

    async def get_outlet_response_by_id(  # Для эндпоинта GET /outlets/{outlet_id}
        self,
        session: AsyncSession,
        outlet_model: OutletModel,  # outlet_model из зависимости get_verified_outlet
    ) -> OutletResponse:
        # outlet_model уже проверен на доступ и активен
        return OutletResponse.model_validate(outlet_model)

    async def get_outlet(self, outlet: OutletModel) -> OutletResponse:
        try:
            return OutletResponse.model_validate(outlet)
        except ValidationError as e:
            logger.error(
                f"Failed to validate outlet {outlet.id} in get_outlet: {e}",
                exc_info=True,
            )
            raise InternalServerError(
                detail="Internal data validation error.",
                internal_details={
                    "outlet_id": outlet.id,
                    "validation_errors": e.errors(),
                },
            )

    async def update_outlet(
        self,
        session: AsyncSession,
        outlet_to_update: OutletModel,  # Из зависимости get_verified_outlet
        update_data: OutletUpdate,
    ) -> OutletResponse:
        update_data_dict = update_data.model_dump(exclude_unset=True)

        # Проверка на уникальность имени, если оно меняется
        if (
            "name" in update_data_dict
            and update_data_dict["name"] != outlet_to_update.name
        ):
            existing_outlet_by_name = await self.dao.outlet.get_by_name_and_company_id(
                session,
                name=update_data_dict["name"],
                company_id=outlet_to_update.company_id,
            )
            if (
                existing_outlet_by_name
            ):  # get_by_name_and_company_id уже ищет не удаленные
                raise OutletNameConflictInCompanyException(
                    name=update_data_dict["name"],
                    company_id=outlet_to_update.company_id,
                )

        updated_outlet_model = await self.dao.outlet.update(
            session, db_obj=outlet_to_update, obj_in=update_data_dict
        )

        if not updated_outlet_model:
            raise OutletNotFoundException(
                identifier=outlet_to_update.id,
            )
        return OutletResponse.model_validate(updated_outlet_model)

    async def archive_outlet(
        self,
        session: AsyncSession,
        outlet_to_archive: OutletModel,  # Из зависимости get_verified_outlet
    ) -> OutletResponse:
        archived_outlet_model = await self.dao.outlet.soft_delete(
            session, id_=outlet_to_archive.id
        )  # soft_delete из CRUDBase
        if (
            not archived_outlet_model
        ):  # Если soft_delete вернул None (уже удален или не найден)
            raise OutletNotFoundException(identifier=outlet_to_archive.id)

        # Дополнительно можно изменить статус, если soft_delete его не меняет
        if archived_outlet_model.status != OutletStatusEnum.ARCHIVED:
            archived_outlet_model.status = OutletStatusEnum.ARCHIVED
            session.add(archived_outlet_model)
            await session.flush()
            await session.refresh(archived_outlet_model)
        # Коммит будет автоматическим

        return OutletResponse.model_validate(archived_outlet_model)
