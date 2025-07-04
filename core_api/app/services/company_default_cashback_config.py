# backend/services/cashback_service.py
import decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.holder import HolderDAO
from app.exceptions.common import (  # Добавил ConflictException
    ConflictException,
    NotFoundException,
    ValidationException,
)
from app.models.company import Company as CompanyModel
from app.schemas.company_default_cashback_config import (
    CompanyDefaultCashbackConfigResponse,
    CompanyDefaultCashbackConfigUpdate,
)


class CompanyDefaultCashbackConfigService:
    def __init__(self, dao: HolderDAO):
        self.dao = dao

    async def get_cashback_config(
        self, session: AsyncSession, company: CompanyModel
    ) -> CompanyDefaultCashbackConfigResponse:
        """
        Получает конфигурацию кэшбэка для компании.
        Предполагается, что company.cashback_config уже загружен зависимостью.
        """
        if (
            not company.default_cashback_config
            or company.default_cashback_config.is_deleted
        ):
            raise NotFoundException(
                resource_name="Cashback Configuration", identifier=company.id
            )

        return CompanyDefaultCashbackConfigResponse.model_validate(
            company.default_cashback_config
        )

    async def update_cashback_config(
        self,
        session: AsyncSession,
        company: CompanyModel,
        update_data: CompanyDefaultCashbackConfigUpdate,
    ) -> CompanyDefaultCashbackConfigResponse:
        """
        Обновляет конфигурацию кэшбэка для компании.
        Предполагается, что company.cashback_config уже загружен зависимостью.
        """
        cashback_config_to_update = company.default_cashback_config
        if not cashback_config_to_update or cashback_config_to_update.is_deleted:
            raise NotFoundException(
                resource_name="Cashback Configuration", identifier=company.id
            )

        update_dict = update_data.model_dump(exclude_unset=True)

        updated_config_model = await self.dao.default_company_cashback_config.update(
            session, db_obj=cashback_config_to_update, obj_in=update_dict
        )

        return CompanyDefaultCashbackConfigResponse.model_validate(updated_config_model)
